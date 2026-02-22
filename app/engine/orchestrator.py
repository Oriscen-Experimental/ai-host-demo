import time
import asyncio
from app.models import Session, Stage, Message, STAGE_DURATIONS
from app.task_cards import TASK_CARDS, DEFAULT_SESSION_CARDS
from app.engine.gating import can_ai_speak, detect_silence, SpeakPriority, SpeakCategory
from app.engine.groups import make_pairs, make_trios, assign_help_pairs
from app.services.llm import chat, HOST_SYSTEM_PROMPT, build_context_prompt


class Orchestrator:
    """AI Host brain — drives session through stages."""

    def __init__(self, broadcast_fn):
        """broadcast_fn: async (room_code, message_dict) -> None"""
        self.broadcast = broadcast_fn

    # ─── Public entry points ─────────────────────────────────

    async def start_session(self, room_code: str, session: Session):
        """Called when host clicks start."""
        await self._enter_stage(room_code, session, Stage.ONBOARDING)

    async def on_message(self, room_code: str, session: Session, sender_id: str, text: str):
        """Called when a user sends a chat message."""
        p = session.participants.get(sender_id)
        if not p:
            return
        p.speak_count += 1
        msg = Message(type="user", text=text, speaker_id=sender_id, speaker_name=p.nickname)
        session.add_message(msg)
        await self.broadcast(room_code, {"type": "user_message", "message": msg.to_dict()})

    async def on_submit_onboarding(self, room_code: str, session: Session, sender_id: str, data: dict):
        p = session.participants.get(sender_id)
        if not p:
            return
        p.onboarding = data
        await self.broadcast(room_code, {
            "type": "participant_update",
            "participant": p.to_dict(),
        })
        # Check if all submitted
        connected = session.get_connected_participants()
        if all(p.onboarding for p in connected):
            # AI智能选择任务卡
            from app.services.task_selector import select_tasks_for_session
            session.selected_cards = await select_tasks_for_session(session)

            await self._ai_speak(room_code, session,
                "好的，我根据大家的状态选好了今天的活动环节，让我们开始吧！",
                SpeakPriority.URGENT, force=True)
            await asyncio.sleep(1.5)
            await self._enter_stage(room_code, session, Stage.S1_CHECKIN)

    async def on_submit_output(self, room_code: str, session: Session, sender_id: str, data: dict):
        """User submits a task output (plan form, help request, etc.)."""
        p = session.participants.get(sender_id)
        if not p:
            return
        session.outputs[sender_id] = data
        p.outputs = data
        await self.broadcast(room_code, {
            "type": "output_update",
            "sender_id": sender_id,
            "sender_name": p.nickname,
            "data": data,
        })
        # Stage-specific logic
        if session.stage == Stage.S3_MAIN_FILL:
            connected = session.get_connected_participants()
            if all(pid in session.outputs for pid in [pp.id for pp in connected]):
                await self._ai_speak(room_code, session,
                    "所有人都填好了！现在进入三人组互审改稿环节。",
                    SpeakPriority.URGENT, force=True)
                await asyncio.sleep(1)
                await self._enter_stage(room_code, session, Stage.S3_MAIN_REVIEW)
        elif session.stage == Stage.S4_HELP:
            session.help_requests[sender_id] = data.get("request", "")
            connected = session.get_connected_participants()
            if all(pid in session.help_requests for pid in [pp.id for pp in connected]):
                await self._start_help_respond(room_code, session)

    async def on_help_response(self, room_code: str, session: Session, sender_id: str, data: dict):
        session.help_responses[sender_id] = data.get("response", "")
        await self.broadcast(room_code, {
            "type": "help_response_update",
            "sender_id": sender_id,
            "sender_name": session.participants[sender_id].nickname,
            "data": data,
        })
        connected = session.get_connected_participants()
        if all(pid in session.help_responses for pid in [pp.id for pp in connected]):
            await self._ai_speak(room_code, session,
                "所有人都给出了回应！互助环节完成。",
                SpeakPriority.URGENT, force=True)
            await asyncio.sleep(1)
            await self._enter_stage(room_code, session, Stage.S5_COMMIT)

    async def on_vote(self, room_code: str, session: Session, sender_id: str, target_id: str):
        session.votes[sender_id] = target_id
        await self.broadcast(room_code, {
            "type": "vote_update",
            "votes": session.votes,
        })
        connected = session.get_connected_participants()
        if all(pid in session.votes for pid in [pp.id for pp in connected]):
            await self._generate_commitments(room_code, session)

    async def on_pass_turn(self, room_code: str, session: Session, sender_id: str):
        current = session.get_current_turn_participant()
        if current and current.id == sender_id:
            await self._advance_turn(room_code, session)

    async def on_submit_feedback(self, room_code: str, session: Session, sender_id: str, data: dict):
        p = session.participants.get(sender_id)
        if p:
            p.feedback = data
        connected = session.get_connected_participants()
        if all(pp.feedback for pp in connected):
            await self._enter_stage(room_code, session, Stage.ENDED)

    async def tick(self, room_code: str, session: Session):
        """Called every 10 seconds by timer."""
        if session.stage in (Stage.WAITING, Stage.ENDED):
            return

        remaining = session.timer_remaining()
        await self.broadcast(room_code, {"type": "timer_update", "remaining": remaining})

        # 智能干预：检查是否有新消息，决定是否介入
        if self._has_new_messages(session) and session.stage not in (
            Stage.ONBOARDING, Stage.S3_MAIN_FILL, Stage.ENDED
        ):
            should_speak, response_text = await self._llm_decide_intervention(session)
            if should_speak and response_text:
                await self._ai_speak(room_code, session, response_text, SpeakPriority.NORMAL)

        # Silence detection (fallback)
        if detect_silence(session) and session.stage not in (
            Stage.ONBOARDING, Stage.S3_MAIN_FILL, Stage.ENDED
        ):
            card = session.current_card
            fallback_text = card.fallback if card else "大家可以随时发言，也可以 pass。"
            if can_ai_speak(session, SpeakPriority.URGENT):
                await self._ai_speak(room_code, session, fallback_text, SpeakPriority.URGENT)

        # Timer expired — advance stage
        if remaining <= 0 and session.timer_end > 0:
            await self._on_timer_expired(room_code, session)

    def _has_new_messages(self, session: Session) -> bool:
        """检查最近10秒是否有新用户消息"""
        if not session.messages:
            return False
        # 找最近的用户消息
        for msg in reversed(session.messages):
            if msg.type == "user":
                return (time.time() - msg.timestamp) < 10
        return False

    async def _llm_decide_intervention(self, session: Session) -> tuple[bool, str]:
        """调用LLM判断是否需要介入，返回(是否介入, 介入内容)"""
        context = build_context_prompt(session.to_client_state())
        prompt = f"""根据以下对话上下文，判断AI主持人是否应该说话。

规则：
- 如果对话正常进行中，大家在积极交流，回复 NO_INTERVENTION
- 如果需要介入（鼓励安静的人、总结讨论、推进进度、打断跑题），直接给出要说的话
- 回复简短，1-2句话

当前状态：
{context}"""
        try:
            response = await chat(
                HOST_SYSTEM_PROMPT,
                [{"role": "user", "content": prompt}],
                max_tokens=128,
            )
            if not response or "NO_INTERVENTION" in response.upper():
                return False, ""
            return True, response.strip()
        except Exception as e:
            print(f"[LLM] Intervention decision error: {e}")
            return False, ""

    # ─── Stage transitions ───────────────────────────────────

    async def _enter_stage(self, room_code: str, session: Session, stage: Stage):
        session.stage = stage
        session.turn_index = 0
        session.turn_order = []
        session.groups = []

        duration = STAGE_DURATIONS.get(stage, 0)
        if duration > 0:
            session.set_timer(duration)

        await self.broadcast(room_code, {
            "type": "stage_change",
            "state": session.to_client_state(),
        })

        if stage == Stage.ONBOARDING:
            await self._run_onboarding(room_code, session)
        elif stage == Stage.S1_CHECKIN:
            await self._run_s1(room_code, session)
        elif stage == Stage.S2_MICRO:
            await self._run_s2(room_code, session)
        elif stage == Stage.S3_MAIN:
            await self._enter_stage(room_code, session, Stage.S3_MAIN_FILL)
        elif stage == Stage.S3_MAIN_FILL:
            await self._run_s3_fill(room_code, session)
        elif stage == Stage.S3_MAIN_REVIEW:
            await self._run_s3_review(room_code, session)
        elif stage == Stage.S4_HELP:
            await self._run_s4(room_code, session)
        elif stage == Stage.S5_COMMIT:
            await self._run_s5(room_code, session)
        elif stage == Stage.S6_CLOSING:
            await self._run_s6(room_code, session)
        elif stage == Stage.ENDED:
            await self._run_ended(room_code, session)

    async def _on_timer_expired(self, room_code: str, session: Session):
        """Handle timer expiration for current stage."""
        session.timer_end = 0
        stage = session.stage
        next_stage_map = {
            Stage.ONBOARDING: Stage.S1_CHECKIN,
            Stage.S1_CHECKIN: Stage.S2_MICRO,
            Stage.S2_MICRO: Stage.S3_MAIN,
            Stage.S3_MAIN_FILL: Stage.S3_MAIN_REVIEW,
            Stage.S3_MAIN_REVIEW: Stage.S4_HELP,
            Stage.S4_HELP: Stage.S4_HELP_RESPOND,
            Stage.S4_HELP_RESPOND: Stage.S5_COMMIT,
            Stage.S5_COMMIT: Stage.S6_CLOSING,
            Stage.S6_CLOSING: Stage.ENDED,
        }
        next_stage = next_stage_map.get(stage)
        if next_stage:
            await self._ai_speak(room_code, session,
                "时间到！我们进入下一个环节。",
                SpeakPriority.URGENT, force=True)
            await asyncio.sleep(1)
            await self._enter_stage(room_code, session, next_stage)

    # ─── Stage implementations ───────────────────────────────

    async def _run_onboarding(self, room_code: str, session: Session):
        await self.broadcast(room_code, {"type": "show_onboarding"})
        await self._ai_speak(room_code, session,
            "欢迎大家！请先花 1 分钟填写快速问卷，帮助我了解大家的状态。",
            SpeakPriority.URGENT, force=True)

    async def _run_s1(self, room_code: str, session: Session):
        card_id = session.selected_cards.get("opening", "CARD_10")
        card = TASK_CARDS[card_id]
        session.current_card = card
        pids = [p.id for p in session.get_connected_participants()]
        session.turn_order = pids
        session.turn_index = 0

        await self.broadcast(room_code, {
            "type": "show_card",
            "card": session.to_client_state()["current_card"],
        })

        opening = (
            "欢迎大家。三条规则：随时可以 pass；不深挖隐私；不推销不攻击。\n"
            "今天我们会做 1 个主任务 + 2 个微任务，保证不尬聊且有产出。\n\n"
            f"现在快速轮一圈，每人 20 秒。说两件事：\n"
            f"1) 能量 1–5\n2) 你今天更想要：倾听 / 建议 / 一起做事 / 轻松一下\n\n"
        )
        first = session.participants.get(pids[0])
        if first:
            opening += f"先从 {first.nickname} 开始！"

        await self._ai_speak(room_code, session, opening, SpeakPriority.URGENT, force=True)
        await self._broadcast_turn(room_code, session)

    async def _run_s2(self, room_code: str, session: Session):
        card_id = session.selected_cards.get("micro", "CARD_17")
        card = TASK_CARDS[card_id]
        session.current_card = card
        pids = [p.id for p in session.get_connected_participants()]
        session.groups = make_pairs(pids)

        await self.broadcast(room_code, {
            "type": "show_card",
            "card": session.to_client_state()["current_card"],
        })
        await self.broadcast(room_code, {
            "type": "group_assign",
            "groups": session.groups,
            "mode": "PAIRS",
        })

        group_text = self._format_groups(session, "pairs")
        await self._ai_speak(room_code, session,
            f"现在两两一组练习复述。\n{group_text}\n\n"
            "每人 60 秒回答：'你理想的 2 小时小生活是什么？'\n"
            "对方用 20 秒复述你在乎的点，你只纠正 1 点。\n"
            "可以只说关键词，也可以用中文。开始吧！",
            SpeakPriority.URGENT, force=True)

    async def _run_s3_fill(self, room_code: str, session: Session):
        card_id = session.selected_cards.get("main", "CARD_08")
        card = TASK_CARDS[card_id]
        session.current_card = card
        session.outputs = {}

        await self.broadcast(room_code, {
            "type": "show_card",
            "card": session.to_client_state()["current_card"],
        })
        await self.broadcast(room_code, {"type": "show_plan_form"})

        await self._ai_speak(room_code, session,
            "接下来是今天的主任务：每个人产出一条「2 小时微冒险计划」。\n"
            "格式固定 5 项：时间 / 地点 / 预算 / 同伴角色 / 邀请话术。\n"
            "重点：要小到离谱，一周内能发生。\n"
            "大家先安静填写，4 分钟后我们三人一组互相改稿。",
            SpeakPriority.URGENT, force=True)

    async def _run_s3_review(self, room_code: str, session: Session):
        pids = [p.id for p in session.get_connected_participants()]
        session.groups = make_trios(pids)
        session.turn_order = pids
        session.turn_index = 0

        await self.broadcast(room_code, {
            "type": "group_assign",
            "groups": session.groups,
            "mode": "TRIOS",
        })

        group_text = self._format_groups(session, "trios")
        await self._ai_speak(room_code, session,
            f"好的，现在三人一组互审改稿。\n{group_text}\n\n"
            "每人 90 秒读出计划，组员只做两件事：\n"
            "1) 把计划缩小（降低门槛）\n"
            "2) 把邀请话术改得不尬\n\n",
            SpeakPriority.URGENT, force=True)

        first = session.get_current_turn_participant()
        if first:
            await asyncio.sleep(1)
            await self._ai_speak(room_code, session,
                f"先从 {first.nickname} 开始，请读出你的计划！",
                SpeakPriority.URGENT, force=True)
        await self._broadcast_turn(room_code, session)

    async def _run_s4(self, room_code: str, session: Session):
        card_id = session.selected_cards.get("help", "CARD_18")
        card = TASK_CARDS[card_id]
        session.current_card = card
        session.help_requests = {}
        session.help_responses = {}
        session.help_assignments = {}

        await self.broadcast(room_code, {
            "type": "show_card",
            "card": session.to_client_state()["current_card"],
        })
        await self.broadcast(room_code, {"type": "show_help_form"})

        await self._ai_speak(room_code, session,
            "每人写一个「小请求」，必须小到 30 分钟以内能推进一点。\n"
            "不会写就用模板：'我卡在__，想要__'。",
            SpeakPriority.URGENT, force=True)

    async def _start_help_respond(self, room_code: str, session: Session):
        await self._enter_stage(room_code, session, Stage.S4_HELP_RESPOND)
        pids = [p.id for p in session.get_connected_participants()]
        session.help_assignments = assign_help_pairs(pids)

        await self.broadcast(room_code, {
            "type": "help_assignments",
            "assignments": session.help_assignments,
            "requests": session.help_requests,
        })

        await self._ai_speak(room_code, session,
            "所有请求收到！我已经给每人分配了一个要回应的人。\n"
            "请给对方一条可执行回应：下一步是什么，5 分钟能做什么。",
            SpeakPriority.URGENT, force=True)

    async def _run_s5(self, room_code: str, session: Session):
        card_id = session.selected_cards.get("commit", "CARD_05")
        card = TASK_CARDS[card_id]
        session.current_card = card
        session.votes = {}

        await self.broadcast(room_code, {
            "type": "show_card",
            "card": session.to_client_state()["current_card"],
        })
        await self.broadcast(room_code, {
            "type": "show_vote",
            "outputs": session.outputs,
        })

        await self._ai_speak(room_code, session,
            "最后一步：把今晚变成下周会发生的事。\n"
            "你可以点选一张别人的计划：「我愿意加入」，哪怕只加入 60 分钟。\n"
            "我会生成承诺公告。",
            SpeakPriority.URGENT, force=True)

    async def _generate_commitments(self, room_code: str, session: Session):
        commitments = []
        vote_groups: dict[str, list[str]] = {}
        for voter_id, target_id in session.votes.items():
            if target_id not in vote_groups:
                vote_groups[target_id] = [target_id]
            if voter_id != target_id:
                vote_groups[target_id].append(voter_id)

        for target_id, members in vote_groups.items():
            if len(members) >= 2:
                names = [session.participants[m].nickname for m in members if m in session.participants]
                plan = session.outputs.get(target_id, {})
                commitments.append({
                    "members": names,
                    "plan_owner": session.participants.get(target_id, {}).nickname if target_id in session.participants else "?",
                    "plan": plan,
                })

        session.commitments = commitments
        await self.broadcast(room_code, {
            "type": "commitments",
            "commitments": commitments,
        })

        if commitments:
            summary = "本周承诺公告：\n"
            for c in commitments:
                summary += f"• {' + '.join(c['members'])} 一起执行 {c['plan_owner']} 的计划\n"
            await self._ai_speak(room_code, session, summary, SpeakPriority.URGENT, force=True)
        else:
            await self._ai_speak(room_code, session,
                "没关系，即使没有配对，每个人的计划本身就是一个承诺。",
                SpeakPriority.URGENT, force=True)

        await asyncio.sleep(2)
        await self._enter_stage(room_code, session, Stage.S6_CLOSING)

    async def _run_s6(self, room_code: str, session: Session):
        session.current_card = None
        await self.broadcast(room_code, {"type": "show_feedback"})

        pids = [p.id for p in session.get_connected_participants()]
        session.turn_order = pids
        session.turn_index = 0

        await self._ai_speak(room_code, session,
            "每人一句：'我今天从谁那里拿走了什么（具体一点）'。\n"
            "然后请填写 20 秒的反馈问卷。",
            SpeakPriority.URGENT, force=True)
        await self._broadcast_turn(room_code, session)

    async def _run_ended(self, room_code: str, session: Session):
        await self._ai_speak(room_code, session,
            "感谢大家参与！今天的 session 结束了。\n"
            "希望你们带走了一些具体的东西——一个计划、一个承诺、或一个新朋友。下次见！",
            SpeakPriority.URGENT, force=True)

    # ─── Helpers ─────────────────────────────────────────────

    async def _ai_speak(self, room_code: str, session: Session, text: str,
                        priority: str = SpeakPriority.NORMAL,
                        category: str = SpeakCategory.STAGE_TRANSITION,
                        force: bool = False):
        if not force and not can_ai_speak(session, priority, category):
            return
        msg = Message(type="ai", text=text, speaker_name="AI 主持人")
        session.add_message(msg)
        await self.broadcast(room_code, {"type": "ai_message", "message": msg.to_dict()})

    async def _ai_speak_llm(self, room_code: str, session: Session, user_prompt: str,
                            priority: str = SpeakPriority.NORMAL,
                            category: str = SpeakCategory.SUMMARY):
        if not can_ai_speak(session, priority, category):
            return
        context = build_context_prompt(session.to_client_state())
        try:
            response = await chat(
                HOST_SYSTEM_PROMPT,
                [
                    {"role": "user", "content": f"当前状态:\n{context}\n\n{user_prompt}"},
                ],
                max_tokens=256,
            )
            if response:
                await self._ai_speak(room_code, session, response.strip(), priority, category, force=True)
        except Exception as e:
            print(f"[LLM] Error: {e}")

    async def _broadcast_turn(self, room_code: str, session: Session):
        current = session.get_current_turn_participant()
        await self.broadcast(room_code, {
            "type": "turn_change",
            "turn_index": session.turn_index,
            "turn_order": session.turn_order,
            "current_id": current.id if current else None,
            "current_name": current.nickname if current else None,
        })

    async def _advance_turn(self, room_code: str, session: Session):
        has_next = session.advance_turn()
        if has_next:
            current = session.get_current_turn_participant()
            if current:
                await self._ai_speak(room_code, session,
                    f"下一位：{current.nickname}！",
                    SpeakPriority.NORMAL, SpeakCategory.TURN_PROMPT)
            await self._broadcast_turn(room_code, session)
        else:
            # All turns done — advance stage
            next_stage_map = {
                Stage.S1_CHECKIN: Stage.S2_MICRO,
                Stage.S3_MAIN_REVIEW: Stage.S4_HELP,
                Stage.S6_CLOSING: Stage.ENDED,
            }
            next_stage = next_stage_map.get(session.stage)
            if next_stage:
                await self._ai_speak(room_code, session,
                    "好的，这一轮结束了！",
                    SpeakPriority.URGENT, force=True)
                await asyncio.sleep(1)
                await self._enter_stage(room_code, session, next_stage)

    def _format_groups(self, session: Session, mode: str) -> str:
        lines = []
        label = "组" if mode == "trios" else "组"
        for i, group in enumerate(session.groups):
            names = [session.participants[pid].nickname for pid in group if pid in session.participants]
            lines.append(f"  {label}{i+1}: {' + '.join(names)}")
        return "\n".join(lines)
