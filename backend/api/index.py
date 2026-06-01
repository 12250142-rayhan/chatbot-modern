from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://chatbot-modern.vercel.app",
        "https://r-hospital-chatbot.vercel.app",
        "https://chatbot-modern-12250142-rayhans-projects.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "R Hospital Backend is running"
    }


@app.get("/test")
def test():
    return {
        "status": "ok"
    }


@app.post("/chat")
def chat(request: dict):
    user_message = request.get("message", "")

    return {
        "reply": f"Backend berhasil menerima pesan: {user_message}"
    }