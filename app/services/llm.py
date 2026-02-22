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


HOST_SYSTEM_PROMPT = """You are an AI moderator for group activities. Your task is to guide 2-6 people through a 75-minute structured social activity.

Your core principles:
1. Brief and warm: Keep each response to 2-3 sentences max, friendly but not overly enthusiastic
2. Control flow and time: Strictly follow the stage flow, remind when time is running out
3. Fair rotation: Ensure everyone gets a chance to speak, don't let one person dominate
4. Lower barriers: Provide "minimum version" for any task, allow pass, text-only, or just listening
5. No lecturing or psychologizing: Don't judge, analyze, or give big lessons - just move the task forward
6. Concrete outcomes: Each stage should have specific outputs, not just chatting

Speak in a conversational tone, like a reliable friend organizing an activity, not a teacher or formal host."""


def build_context_prompt(session_state: dict) -> str:
    """Build context for the AI based on current session state."""
    stage = session_state.get("stage", "")
    participants = session_state.get("participants", {})
    card = session_state.get("current_card")
    timer = session_state.get("timer_remaining", 0)
    messages = session_state.get("messages", [])

    parts = [f"Current stage: {session_state.get('stage_name', stage)}"]
    parts.append(f"Time remaining: {timer} seconds")
    parts.append(f"Participants: {', '.join(p['nickname'] for p in participants.values())}")

    if card:
        parts.append(f"Current task card: {card['title']}")
        parts.append(f"Goal: {card['goal']}")
        parts.append(f"Steps: {'; '.join(card['steps'])}")

    if session_state.get("turn_order"):
        turn_idx = session_state.get("turn_index", 0)
        if turn_idx < len(session_state["turn_order"]):
            current_pid = session_state["turn_order"][turn_idx]
            current_name = participants.get(current_pid, {}).get("nickname", "?")
            parts.append(f"Current turn: {current_name}")

    recent = messages[-20:] if messages else []
    if recent:
        parts.append("Recent conversation:")
        for m in recent:
            name = m.get("speaker_name", "System") if m["type"] != "ai" else "AI Host"
            parts.append(f"  {name}: {m['text']}")

    return "\n".join(parts)
