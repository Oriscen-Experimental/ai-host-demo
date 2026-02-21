import uuid
from fastapi import WebSocket
from app.models import Session, Stage
from app.engine.orchestrator import Orchestrator
from app.engine.timer import SessionTimer
from app.config import MAX_PARTICIPANTS


class ConnectionManager:
    def __init__(self):
        # room_code -> list of (websocket, participant_id)
        self.rooms: dict[str, list[tuple[WebSocket, str]]] = {}
        self.ws_to_pid: dict[WebSocket, str] = {}
        self.orchestrator = Orchestrator(broadcast_fn=self.broadcast)
        self.timers: dict[str, SessionTimer] = {}

    async def connect(self, websocket: WebSocket, room_code: str):
        await websocket.accept()
        if room_code not in self.rooms:
            self.rooms[room_code] = []

    def disconnect(self, websocket: WebSocket, room_code: str, session: Session):
        pid = self.ws_to_pid.pop(websocket, None)
        if room_code in self.rooms:
            self.rooms[room_code] = [
                (ws, p) for ws, p in self.rooms[room_code] if ws != websocket
            ]
        if pid:
            session.remove_participant(pid)

    async def broadcast(self, room_code: str, message: dict):
        if room_code not in self.rooms:
            return
        dead = []
        for ws, pid in self.rooms[room_code]:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.rooms[room_code] = [
                (w, p) for w, p in self.rooms[room_code] if w != ws
            ]

    async def send_to(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_json(message)
        except Exception:
            pass

    async def handle_message(self, websocket: WebSocket, room_code: str, session: Session, data: dict):
        msg_type = data.get("type", "")

        if msg_type == "join":
            await self._handle_join(websocket, room_code, session, data)
        elif msg_type == "start_session":
            await self._handle_start(websocket, room_code, session)
        elif msg_type == "chat":
            pid = self.ws_to_pid.get(websocket, "")
            text = data.get("text", "").strip()
            if pid and text:
                await self.orchestrator.on_message(room_code, session, pid, text)
        elif msg_type == "submit_onboarding":
            pid = self.ws_to_pid.get(websocket, "")
            if pid:
                await self.orchestrator.on_submit_onboarding(room_code, session, pid, data.get("data", {}))
        elif msg_type == "submit_output":
            pid = self.ws_to_pid.get(websocket, "")
            if pid:
                await self.orchestrator.on_submit_output(room_code, session, pid, data.get("data", {}))
        elif msg_type == "submit_help_response":
            pid = self.ws_to_pid.get(websocket, "")
            if pid:
                await self.orchestrator.on_help_response(room_code, session, pid, data.get("data", {}))
        elif msg_type == "pass_turn":
            pid = self.ws_to_pid.get(websocket, "")
            if pid:
                await self.orchestrator.on_pass_turn(room_code, session, pid)
        elif msg_type == "vote":
            pid = self.ws_to_pid.get(websocket, "")
            target = data.get("target_id", "")
            if pid and target:
                await self.orchestrator.on_vote(room_code, session, pid, target)
        elif msg_type == "submit_feedback":
            pid = self.ws_to_pid.get(websocket, "")
            if pid:
                await self.orchestrator.on_submit_feedback(room_code, session, pid, data.get("data", {}))
        elif msg_type == "next_turn":
            pid = self.ws_to_pid.get(websocket, "")
            if pid:
                await self.orchestrator.on_pass_turn(room_code, session, pid)

    async def _handle_join(self, websocket: WebSocket, room_code: str, session: Session, data: dict):
        nickname = data.get("nickname", "").strip()
        if not nickname:
            await self.send_to(websocket, {"type": "error", "message": "请输入昵称"})
            return

        if len(session.get_connected_participants()) >= MAX_PARTICIPANTS:
            await self.send_to(websocket, {"type": "error", "message": "房间已满"})
            return

        if session.stage != Stage.WAITING:
            await self.send_to(websocket, {"type": "error", "message": "活动已开始，无法加入"})
            return

        pid = str(uuid.uuid4())[:8]
        participant = session.add_participant(pid, nickname)
        self.ws_to_pid[websocket] = pid
        self.rooms[room_code].append((websocket, pid))

        await self.send_to(websocket, {
            "type": "joined",
            "participant_id": pid,
            "is_host": participant.is_host,
            "state": session.to_client_state(),
        })

        await self.broadcast(room_code, {
            "type": "participant_joined",
            "participant": participant.to_dict(),
            "state": session.to_client_state(),
        })

    async def _handle_start(self, websocket: WebSocket, room_code: str, session: Session):
        pid = self.ws_to_pid.get(websocket, "")
        if pid != session.host_id:
            await self.send_to(websocket, {"type": "error", "message": "只有房主可以开始"})
            return

        connected = session.get_connected_participants()
        if len(connected) < 2:
            await self.send_to(websocket, {"type": "error", "message": "至少需要 2 人"})
            return

        # Start the tick timer
        timer = SessionTimer(room_code, self._tick_callback)
        self.timers[room_code] = timer
        timer.start()

        await self.orchestrator.start_session(room_code, session)

    async def _tick_callback(self, room_code: str):
        from app.main import sessions
        session = sessions.get(room_code)
        if session and session.stage != Stage.ENDED:
            await self.orchestrator.tick(room_code, session)


manager = ConnectionManager()
