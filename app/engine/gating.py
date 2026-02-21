import time
from app.models import Session
from app.config import AI_COOLDOWN_SECONDS, AI_NO_INTERRUPT_WINDOW, SILENCE_THRESHOLD


class SpeakPriority:
    NORMAL = "NORMAL"
    URGENT = "URGENT"


class SpeakCategory:
    STAGE_TRANSITION = "stage_transition"
    TURN_PROMPT = "turn_prompt"
    SUMMARY = "summary"
    FALLBACK = "fallback"
    TIMEOUT_WARNING = "timeout_warning"


ALLOWED_NORMAL_CATEGORIES = {
    SpeakCategory.STAGE_TRANSITION,
    SpeakCategory.TURN_PROMPT,
    SpeakCategory.SUMMARY,
    SpeakCategory.TIMEOUT_WARNING,
}


def can_ai_speak(session: Session, priority: str, category: str = "") -> bool:
    """
    Gate AI speech based on hard rules.
    Returns True if AI is allowed to speak.
    """
    now = time.time()

    if priority == SpeakPriority.URGENT:
        return True

    # NORMAL rules
    time_since_last_ai = now - session.last_ai_speak_at
    if time_since_last_ai < AI_COOLDOWN_SECONDS:
        return False

    time_since_last_user = now - session.last_user_message_at
    if session.last_user_message_at > 0 and time_since_last_user < AI_NO_INTERRUPT_WINDOW:
        return False

    if category and category not in ALLOWED_NORMAL_CATEGORIES:
        return False

    return True


def detect_silence(session: Session) -> bool:
    """Check if there's been prolonged silence (> threshold)."""
    now = time.time()
    if session.last_user_message_at == 0:
        time_since = now - session.created_at
    else:
        time_since = now - session.last_user_message_at
    return time_since > SILENCE_THRESHOLD
