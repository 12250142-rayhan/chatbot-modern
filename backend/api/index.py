from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
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