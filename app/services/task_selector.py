"""
AI Intelligent Task Selector
Select appropriate task cards based on participant onboarding information
"""
import json
from app.models import Session, Participant
from app.task_cards import TASK_CARDS, DEFAULT_SESSION_CARDS
from app.services.llm import chat


# Task card category pools
CARD_POOLS = {
    "opening": ["CARD_10"],  # Mood weather report
    "micro": ["CARD_02", "CARD_17", "CARD_09", "CARD_14"],  # Micro tasks
    "main": ["CARD_01", "CARD_03", "CARD_04", "CARD_08", "CARD_06", "CARD_16"],  # Main tasks
    "help": ["CARD_18", "CARD_11", "CARD_04"],  # Mutual help type
    "commit": ["CARD_05", "CARD_12", "CARD_13"],  # Commitment landing type
    "rescue": ["CARD_15", "CARD_19", "CARD_07"],  # Rescue/low energy type
}


def _summarize_onboarding(participants: list[Participant]) -> str:
    """Summarize all participants' onboarding information"""
    if not participants:
        return "No participant information"

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

        # Energy level
        energy = ob.get("energy", 3)
        energies.append(energy)

        # Social goals
        goal = ob.get("goal", "")
        if goal:
            goals.append(goal)

        # Interests
        interest = ob.get("interest", "")
        if interest:
            interests.append(interest)

        # Age range
        age = ob.get("age", "")
        if age and age != "prefer_not":
            ages.append(age)

        # Slow to warm up
        if ob.get("shy") == "yes":
            shys += 1

        # Willing to take action
        if ob.get("action") == "yes":
            willing_action += 1

    avg_energy = sum(energies) / len(energies) if energies else 3

    lines = [
        f"Number of people: {n}",
        f"Average energy: {avg_energy:.1f}/5",
        f"Slow to warm up: {shys}/{n}",
        f"Willing to take action: {willing_action}/{n}",
    ]

    if goals:
        goal_summary = ", ".join(set(goals))
        lines.append(f"Social goals: {goal_summary}")

    if interests:
        interest_summary = ", ".join(set(interests))
        lines.append(f"Interest areas: {interest_summary}")

    if ages:
        age_summary = ", ".join(set(ages))
        lines.append(f"Age distribution: {age_summary}")

    return "\n".join(lines)


def _format_card_pools() -> str:
    """Format task card pools for LLM reference"""
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
    """Parse LLM selection result with fallback"""
    try:
        # Try to extract JSON
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = response[start:end]
            result = json.loads(json_str)

            # Validate selected cards exist
            validated = {}
            for slot, card_id in result.items():
                if card_id in TASK_CARDS:
                    validated[slot] = card_id
                elif slot in DEFAULT_SESSION_CARDS:
                    validated[slot] = DEFAULT_SESSION_CARDS[slot]

            # Fill in missing slots
            for slot in DEFAULT_SESSION_CARDS:
                if slot not in validated:
                    validated[slot] = DEFAULT_SESSION_CARDS[slot]

            return validated
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"[TaskSelector] Parse error: {e}")

    # Parse failed, return default
    return DEFAULT_SESSION_CARDS.copy()


async def select_tasks_for_session(session: Session) -> dict[str, str]:
    """
    Intelligently select task cards based on onboarding information
    Returns: {"opening": "CARD_XX", "micro": "CARD_XX", ...}
    """
    participants = session.get_connected_participants()

    if not participants or not any(p.onboarding for p in participants):
        return DEFAULT_SESSION_CARDS.copy()

    # Summarize onboarding data
    summary = _summarize_onboarding(participants)
    card_pools = _format_card_pools()

    # Build prompt
    prompt = f"""Based on participant information, select appropriate task cards for this group activity.

## Participant Summary
{summary}

## Available Task Card Pools
{card_pools}

## Selection Principles
1. Low energy group (<3): Choose low-risk, short-duration cards
2. Many slow-to-warm-up (>50%): Choose gradual icebreakers, low-pressure cards
3. Social goal is "casual chat": Choose relaxed cards
4. Few willing to take action: Main task can be lighter
5. Maintain variety: Different styles for different stages

Please select one card ID for each slot. Return JSON only, format:
{{"opening": "CARD_XX", "micro": "CARD_XX", "main": "CARD_XX", "help": "CARD_XX", "commit": "CARD_XX", "rescue": "CARD_XX"}}
"""

    try:
        response = await chat(
            "",  # No system prompt needed
            [{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        selected = _parse_selection(response)
        print(f"[TaskSelector] Selected cards: {selected}")
        return selected
    except Exception as e:
        print(f"[TaskSelector] Error: {e}")
        return DEFAULT_SESSION_CARDS.copy()
