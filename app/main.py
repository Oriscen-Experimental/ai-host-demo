from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pathlib import Path
import string
import random

from app.ws.handler import manager
from app.models import Session

app = FastAPI(title="AI Host - Group Activity AI Moderator")

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# In-memory session store
sessions: dict[str, Session] = {}


def generate_room_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/rooms")
async def create_room():
    code = generate_room_code()
    while code in sessions:
        code = generate_room_code()
    sessions[code] = Session(code=code)
    return {"code": code}


@app.get("/api/rooms/{code}")
async def get_room(code: str):
    session = sessions.get(code)
    if not session:
        return JSONResponse(status_code=404, content={"error": "Room does not exist"})
    return session.to_client_state()


@app.get("/api/health")
async def health():
    return {"status": "ok", "rooms": len(sessions)}


@app.websocket("/ws/{room_code}")
async def websocket_endpoint(websocket: WebSocket, room_code: str):
    session = sessions.get(room_code)
    if not session:
        await websocket.close(code=4004, reason="Room does not exist")
        return

    await manager.connect(websocket, room_code)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.handle_message(websocket, room_code, session, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_code, session)
