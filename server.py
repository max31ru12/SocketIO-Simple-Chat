from random import randint

from socketio import ASGIApp, AsyncServer
from fastapi import FastAPI
import uvicorn

app = FastAPI()

sio = AsyncServer(async_mode="asgi", cors_allowed_origins='*')
socketio_app = ASGIApp(
    socketio_server=sio,
    other_asgi_app=app,
)

RIDDLES = [
    ("Загадка 1", "Ответ 1"),
    ("Загадка 2", "Ответ 2"),
    ("Загадка 3", "Ответ 3"),
    ("Загадка 4", "Ответ 4"),
]

passed = []

scores = {}


async def generate_riddle():
    return RIDDLES[randint(0, len(RIDDLES) - 1)][0]


@sio.event
async def connect(sid, environ):
    scores[sid] = 0
    pass


@sio.event
async def disconnect(sid):
    pass


@sio.on("next")
async def give_riddle(sid, data):
    riddle = await generate_riddle()
    if riddle not in passed:
        passed.append(riddle)
        await sio.emit(event="riddle", to=sid, data={"text": riddle})
    else:
        await sio.emit(event="over", to=sid)


@sio.on("answer")
async def give_answer(sid, data):
    is_correct = True if passed[-1][1] == data["text"] else False
    await sio.emit(event="result", to=sid, data={
        "riddle": passed[-1][0],
        "is_correct": is_correct,
        "answer": passed[-1][1]
    })
    if is_correct:
        scores[sid] += 1
    await sio.emit(event="score", to=sid, data={"value": scores[sid]})




if __name__ == "__main__":
    uvicorn.run(socketio_app, host='0.0.0.0', port=8000)
