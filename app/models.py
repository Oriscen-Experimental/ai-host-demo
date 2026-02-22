from enum import Enum
from dataclasses import dataclass, field
import time


class Stage(str, Enum):
    WAITING = "WAITING"
    ONBOARDING = "ONBOARDING"
    S1_CHECKIN = "S1_CHECKIN"
    S2_MICRO = "S2_MICRO"
    S3_MAIN = "S3_MAIN"
    S3_MAIN_FILL = "S3_MAIN_FILL"
    S3_MAIN_REVIEW = "S3_MAIN_REVIEW"
    S4_HELP = "S4_HELP"
    S4_HELP_RESPOND = "S4_HELP_RESPOND"
    S5_COMMIT = "S5_COMMIT"
    S6_CLOSING = "S6_CLOSING"
    ENDED = "ENDED"


class CardMode(str, Enum):
    WHOLE_GROUP = "WHOLE_GROUP"
    PAIRS = "PAIRS"
    TRIOS = "TRIOS"


class OutputType(str, Enum):
    NONE = "NONE"
    TEXT = "TEXT"
    LIST = "LIST"
    AUDIO = "AUDIO"
    IMAGE = "IMAGE"
    LINK = "LINK"
    FORM = "FORM"


STAGE_NAMES = {
    Stage.WAITING: "等待加入",
    Stage.ONBOARDING: "S0 快速了解",
    Stage.S1_CHECKIN: "S1 签到",
    Stage.S2_MICRO: "S2 微任务：被理解",
    Stage.S3_MAIN: "S3 主任务：微冒险计划",
    Stage.S3_MAIN_FILL: "S3 主任务：填写计划",
    Stage.S3_MAIN_REVIEW: "S3 主任务：互审改稿",
    Stage.S4_HELP: "S4 互助请求",
    Stage.S4_HELP_RESPOND: "S4 互助回应",
    Stage.S5_COMMIT: "S5 承诺落地",
    Stage.S6_CLOSING: "S6 收尾反馈",
    Stage.ENDED: "已结束",
}

STAGE_DURATIONS = {
    Stage.ONBOARDING: 180,
    Stage.S1_CHECKIN: 480,
    Stage.S2_MICRO: 720,
    Stage.S3_MAIN_FILL: 240,
    Stage.S3_MAIN_REVIEW: 1860,
    Stage.S4_HELP: 300,
    Stage.S4_HELP_RESPOND: 300,
    Stage.S5_COMMIT: 300,
    Stage.S6_CLOSING: 120,
}


@dataclass
class TaskCard:
    id: str
    title: str
    duration_min: int
    mode: CardMode
    goal: str
    steps: list[str]
    output: OutputType
    agent_script: str
    fallback: str
    tags: list[str]
    safety_notes: str


@dataclass
class Participant:
    id: str
    nickname: str
    is_host: bool = False
    is_connected: bool = True
    speak_count: int = 0
    onboarding: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)
    feedback: dict | None = None

    def to_dict(self):
        return {
            "id": self.id,
            "nickname": self.nickname,
            "is_host": self.is_host,
            "is_connected": self.is_connected,
            "speak_count": self.speak_count,
            "has_onboarding": bool(self.onboarding),
            "has_output": bool(self.outputs),
        }


@dataclass
class Message:
    type: str  # "ai", "user", "system"
    text: str
    speaker_id: str = ""
    speaker_name: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "type": self.type,
            "text": self.text,
            "speaker_id": self.speaker_id,
            "speaker_name": self.speaker_name,
            "timestamp": self.timestamp,
        }


class Session:
    def __init__(self, code: str):
        self.code = code
        self.stage = Stage.WAITING
        self.participants: dict[str, Participant] = {}
        self.host_id: str | None = None
        self.current_card: TaskCard | None = None
        self.turn_order: list[str] = []
        self.turn_index: int = 0
        self.timer_end: float = 0
        self.groups: list[list[str]] = []
        self.messages: list[Message] = []
        self.outputs: dict[str, dict] = {}
        self.commitments: list[dict] = []
        self.votes: dict[str, str] = {}
        self.help_requests: dict[str, str] = {}
        self.help_assignments: dict[str, str] = {}
        self.help_responses: dict[str, str] = {}
        self.created_at: float = time.time()
        self.last_user_message_at: float = 0
        self.last_ai_speak_at: float = 0
        self.sub_stage_data: dict = {}
        self.selected_cards: dict[str, str] = {}  # AI选择的任务卡 {"opening": "CARD_XX", ...}

    def add_participant(self, pid: str, nickname: str) -> Participant:
        is_host = len(self.participants) == 0
        p = Participant(id=pid, nickname=nickname, is_host=is_host)
        self.participants[pid] = p
        if is_host:
            self.host_id = pid
        return p

    def remove_participant(self, pid: str):
        if pid in self.participants:
            self.participants[pid].is_connected = False

    def get_connected_participants(self) -> list[Participant]:
        return [p for p in self.participants.values() if p.is_connected]

    def get_current_turn_participant(self) -> Participant | None:
        if not self.turn_order:
            return None
        if self.turn_index >= len(self.turn_order):
            return None
        pid = self.turn_order[self.turn_index]
        return self.participants.get(pid)

    def advance_turn(self) -> bool:
        """Advance to next turn. Returns False if all turns done."""
        self.turn_index += 1
        return self.turn_index < len(self.turn_order)

    def set_timer(self, seconds: int):
        self.timer_end = time.time() + seconds

    def timer_remaining(self) -> int:
        return max(0, int(self.timer_end - time.time()))

    def add_message(self, msg: Message):
        self.messages.append(msg)
        if msg.type == "user":
            self.last_user_message_at = time.time()
        elif msg.type == "ai":
            self.last_ai_speak_at = time.time()

    def to_client_state(self) -> dict:
        return {
            "code": self.code,
            "stage": self.stage.value,
            "stage_name": STAGE_NAMES.get(self.stage, ""),
            "participants": {
                pid: p.to_dict() for pid, p in self.participants.items()
            },
            "host_id": self.host_id,
            "current_card": {
                "id": self.current_card.id,
                "title": self.current_card.title,
                "duration_min": self.current_card.duration_min,
                "mode": self.current_card.mode.value,
                "goal": self.current_card.goal,
                "steps": self.current_card.steps,
                "output": self.current_card.output.value,
                "agent_script": self.current_card.agent_script,
                "fallback": self.current_card.fallback,
            } if self.current_card else None,
            "turn_order": self.turn_order,
            "turn_index": self.turn_index,
            "timer_remaining": self.timer_remaining(),
            "groups": self.groups,
            "outputs": self.outputs,
            "commitments": self.commitments,
            "votes": self.votes,
            "help_requests": self.help_requests,
            "help_assignments": self.help_assignments,
            "help_responses": self.help_responses,
            "messages": [m.to_dict() for m in self.messages[-50:]],
        }
