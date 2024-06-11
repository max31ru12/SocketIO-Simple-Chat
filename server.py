import sys
from collections import defaultdict
from typing import Any

import uvicorn
from loguru import logger
from pydantic import ValidationError
from socketio import AsyncServer, ASGIApp  # noqa

from schemas import JoinMessage, User, Message

sio = AsyncServer(cors_allowed_origins="*", async_mode="asgi")
app = ASGIApp(socketio_server=sio)

logging_format = "<green>{time}</green> <level>{message}</level>"
logger.add(sys.stdout, format=logging_format, level="ERROR")

room_list = ["lobby", "general", "random"]

rooms = {
    "lobby": [],
    "general": [],
    "random": [],
}

users_storage: dict[str, User] = {}


@sio.event
async def connect(sid: str, environ: dict[Any]) -> None:
    logger.info(f"Подключился {sid=}")


@sio.event
async def disconnect(sid: str) -> None:
    logger.info(f"Отключился {sid=}")


@sio.on("get_rooms")
async def get_rooms(sid: str, data) -> None:
    logger.info("get_rooms was requested")
    await sio.emit("rooms", to=sid, data=room_list)


@sio.on("join")
async def join_room(sid, data) -> None:
    try:
        data: dict[str, str] = JoinMessage(**data).model_dump()
        rooms[data["room"]].append(sid)
        users_storage[sid] = User(**data)

        await sio.emit(event="move", to=sid, data={"room": data["room"]})
        await sio.save_session(sid=sid, session=data)
        await sio.enter_room(sid, data["room"])

        logger.debug(f"{sid} entered room {data['room']}, added session")
    except ValidationError as e:
        logger.error(e.json())
        await sio.emit(event="move", to=sid, data=e.json())


@sio.on("leave")
async def leave_room(sid: str, data) -> None:
    session = await sio.get_session(sid)
    rooms[session["room"]].remove(sid)
    await sio.leave_room(sid, session["room"])
    logger.info(f"{sid} leaved room {session['room']}")
    session["room"] = ""


@sio.on("send_message")
async def send_message(sid: str, data) -> None:
    user = users_storage[sid]
    try:
        message = Message(author=user.model_dump()["name"], **data)
        user.messages.append(message)
        await sio.emit("message", room=user.room, data={"name": user.name,
                                                        "text": message.text})
    except ValidationError as e:
        logger.error(e.json())


if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=80)
