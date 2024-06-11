from pydantic import BaseModel, Field


class JoinMessage(BaseModel):
    room: str = Field()
    name: str = Field()


class Message(BaseModel):
    text: str
    author: str


class User(BaseModel):
    room: str
    name: str
    messages: list[Message] = []
