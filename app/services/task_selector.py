"""
AI智能任务选择器
根据参与者的onboarding信息选择合适的任务卡
"""
import json
from app.models import Session, Participant
from app.task_cards import TASK_CARDS, DEFAULT_SESSION_CARDS
from app.services.llm import chat


# 任务卡分类池
CARD_POOLS = {
    "opening": ["CARD_10"],  # 情绪天气预报
    "micro": ["CARD_02", "CARD_17", "CARD_09", "CARD_14"],  # 微任务
    "main": ["CARD_01", "CARD_03", "CARD_04", "CARD_08", "CARD_06", "CARD_16"],  # 主任务
    "help": ["CARD_18", "CARD_11", "CARD_04"],  # 互助类
    "commit": ["CARD_05", "CARD_12", "CARD_13"],  # 承诺落地类
    "rescue": ["CARD_15", "CARD_19", "CARD_07"],  # 救场/低能量类
}


def _summarize_onboarding(participants: list[Participant]) -> str:
    """汇总所有参与者的onboarding信息"""
    if not participants:
        return "无参与者信息"

    n = len(participants)
    energies = []
    goals = []
    interests = []
    ages = []
    shys = 0
    willing_action = 0

    for p in participants:
        ob = p.onboarding
        if not ob:
            continue

        # 能量等级
        energy = ob.get("energy", 3)
        energies.append(energy)

        # 社交目标
        goal = ob.get("goal", "")
        if goal:
            goals.append(goal)

        # 兴趣
        interest = ob.get("interest", "")
        if interest:
            interests.append(interest)

        # 年龄段
        age = ob.get("age", "")
        if age and age != "prefer_not":
            ages.append(age)

        # 慢热
        if ob.get("shy") == "yes":
            shys += 1

        # 愿意行动
        if ob.get("action") == "yes":
            willing_action += 1

    avg_energy = sum(energies) / len(energies) if energies else 3

    lines = [
        f"人数: {n}人",
        f"平均能量: {avg_energy:.1f}/5",
        f"慢热人数: {shys}/{n}",
        f"愿意行动: {willing_action}/{n}",
    ]

    if goals:
        goal_summary = ", ".join(set(goals))
        lines.append(f"社交目标: {goal_summary}")

    if interests:
        interest_summary = ", ".join(set(interests))
        lines.append(f"兴趣领域: {interest_summary}")

    if ages:
        age_summary = ", ".join(set(ages))
        lines.append(f"年龄分布: {age_summary}")

    return "\n".join(lines)


def _format_card_pools() -> str:
    """格式化任务卡池供LLM参考"""
    lines = []
    for slot, card_ids in CARD_POOLS.items():
        cards_info = []
        for cid in card_ids:
            card = TASK_CARDS.get(cid)
            if card:
                cards_info.append(f"{cid}: {card.title} ({card.mode.value}, {card.duration_min}min)")
        lines.append(f"{slot}: {', '.join(cards_info)}")
    return "\n".join(lines)


def _parse_selection(response: str) -> dict[str, str]:
    """解析LLM返回的选择结果，带兜底"""
    try:
        # 尝试提取JSON
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = response[start:end]
            result = json.loads(json_str)

            # 验证选择的卡都存在
            validated = {}
            for slot, card_id in result.items():
                if card_id in TASK_CARDS:
                    validated[slot] = card_id
                elif slot in DEFAULT_SESSION_CARDS:
                    validated[slot] = DEFAULT_SESSION_CARDS[slot]

            # 补充缺失的slot
            for slot in DEFAULT_SESSION_CARDS:
                if slot not in validated:
                    validated[slot] = DEFAULT_SESSION_CARDS[slot]

            return validated
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"[TaskSelector] Parse error: {e}")

    # 解析失败，返回默认值
    return DEFAULT_SESSION_CARDS.copy()


async def select_tasks_for_session(session: Session) -> dict[str, str]:
    """
    根据onboarding信息智能选择任务卡
    返回: {"opening": "CARD_XX", "micro": "CARD_XX", ...}
    """
    participants = session.get_connected_participants()

    if not participants or not any(p.onboarding for p in participants):
        return DEFAULT_SESSION_CARDS.copy()

    # 汇总onboarding数据
    summary = _summarize_onboarding(participants)
    card_pools = _format_card_pools()

    # 构建prompt
    prompt = f"""根据参与者信息，为这次小组活动选择合适的任务卡。

## 参与者汇总
{summary}

## 可选任务卡池
{card_pools}

## 选择原则
1. 能量低(<3)的群体: 选择低风险、短时间的卡
2. 慢热人数多(>50%): 选择渐进破冰、低压力的卡
3. 社交目标偏"放松聊天": 选择轻松类卡
4. 愿意行动人数少: 主任务可选更轻松的
5. 保持多样性: 不同阶段选不同风格

请为每个slot选择一个卡ID。只返回JSON，格式如下：
{{"opening": "CARD_XX", "micro": "CARD_XX", "main": "CARD_XX", "help": "CARD_XX", "commit": "CARD_XX", "rescue": "CARD_XX"}}
"""

    try:
        response = await chat(
            "",  # 无需system prompt
            [{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        selected = _parse_selection(response)
        print(f"[TaskSelector] Selected cards: {selected}")
        return selected
    except Exception as e:
        print(f"[TaskSelector] Error: {e}")
        return DEFAULT_SESSION_CARDS.copy()
