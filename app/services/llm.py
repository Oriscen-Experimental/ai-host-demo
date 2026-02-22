import app.config as config

_gemini_client = None
_openai_client = None


def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(api_key=config.GOOGLE_API_KEY)
    return _gemini_client


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import AsyncOpenAI
        _openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    return _openai_client


async def chat(system_prompt: str, messages: list[dict], max_tokens: int = 512) -> str:
    """
    Unified LLM chat interface.
    messages: [{"role": "user"|"assistant", "content": "..."}]
    """
    provider = config.LLM_PROVIDER

    if provider == "gemini":
        return await _chat_gemini(system_prompt, messages, max_tokens)
    elif provider == "openai":
        return await _chat_openai(system_prompt, messages, max_tokens)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


async def _chat_gemini(system_prompt: str, messages: list[dict], max_tokens: int) -> str:
    from google.genai import types
    import asyncio

    client = _get_gemini_client()

    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

    def _sync_call():
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
                temperature=0.7,
            ),
        )
        return response.text

    return await asyncio.get_event_loop().run_in_executor(None, _sync_call)


async def _chat_openai(system_prompt: str, messages: list[dict], max_tokens: int) -> str:
    client = _get_openai_client()

    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        api_messages.append({"role": msg["role"], "content": msg["content"]})

    response = await client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=api_messages,
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return response.choices[0].message.content


HOST_SYSTEM_PROMPT = """你是一个小组活动 AI 主持人。你的任务是引导 2-6 个人完成一次 75 分钟的结构化社交活动。

你的核心原则：
1. 简短温暖：每次发言不超过 2-3 句话，语气友好但不过度热情
2. 控场控时：严格按照阶段流程推进，超时要及时提醒
3. 公平轮转：确保每个人都有发言机会，不允许一个人占用太多时间
4. 降低门槛：任何任务都提供"最小版本"，允许 pass、只交文字、只旁听
5. 不说教不心理化：不评判、不分析、不给大道理，只推进任务
6. 收束落地：每个环节要有具体产出，不只是聊天

你说中文。保持口语化，像一个靠谱的朋友在组织活动，不是老师或主持人。"""


def build_context_prompt(session_state: dict) -> str:
    """Build context for the AI based on current session state."""
    stage = session_state.get("stage", "")
    participants = session_state.get("participants", {})
    card = session_state.get("current_card")
    timer = session_state.get("timer_remaining", 0)
    messages = session_state.get("messages", [])

    parts = [f"当前阶段: {session_state.get('stage_name', stage)}"]
    parts.append(f"剩余时间: {timer}秒")
    parts.append(f"参与者: {', '.join(p['nickname'] for p in participants.values())}")

    if card:
        parts.append(f"当前任务卡: {card['title']}")
        parts.append(f"目标: {card['goal']}")
        parts.append(f"步骤: {'; '.join(card['steps'])}")

    if session_state.get("turn_order"):
        turn_idx = session_state.get("turn_index", 0)
        if turn_idx < len(session_state["turn_order"]):
            current_pid = session_state["turn_order"][turn_idx]
            current_name = participants.get(current_pid, {}).get("nickname", "?")
            parts.append(f"当前轮到: {current_name}")

    recent = messages[-20:] if messages else []
    if recent:
        parts.append("最近对话:")
        for m in recent:
            name = m.get("speaker_name", "系统") if m["type"] != "ai" else "AI主持"
            parts.append(f"  {name}: {m['text']}")

    return "\n".join(parts)
