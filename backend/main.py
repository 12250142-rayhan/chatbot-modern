from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from medical_agent import medical_agent


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str
    text: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []


@app.get("/")
def home():
    return {"message": "R Hospital Backend is running"}


@app.post("/chat")
def chat(request: dict):
    user_message = request.get("message", "")
    history = request.get("history", [])

    if waiting_for_registration_choice(history):
        reply = handle_registration_choice(user_message)
        return {
            "reply": reply
        }

    reply = screening_reply(
        user_message,
        history,
        on_duty_doctor=get_on_duty_doctor()
    )

    return {
        "reply": reply
    }