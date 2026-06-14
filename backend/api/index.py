import os
import sys
import requests
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from screening_engine import screening_reply


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://chatbot-modern-eight.vercel.app",
        "https://chatbot-modern.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Default false biar Susan langsung pakai Groq dulu dan tidak pending nunggu Gemini
USE_GEMINI = os.getenv("USE_GEMINI", "false").lower() == "true"


DOCTOR_SCHEDULE = {
    0: {
        "00-08": {"name": "Dr. Rayhan", "phone": "+6398878802928"},
        "08-16": {"name": "Dr. Hapid Mizan", "phone": "+6344878029529"},
        "16-00": {"name": "Dr. Rini Hermi", "phone": "+6342548029777"},
    },
    1: {
        "00-08": {"name": "Dr. Hapid Mizan", "phone": "+6344878029529"},
        "08-16": {"name": "Dr. Rini Hermi", "phone": "+6342548029777"},
        "16-00": {"name": "Dr. Adif Rizal", "phone": "+6342548092021"},
    },
    2: {
        "00-08": {"name": "Dr. Rini Hermi", "phone": "+6342548029777"},
        "08-16": {"name": "Dr. Adif Rizal", "phone": "+6342548092021"},
        "16-00": {"name": "Dr. Rayhan", "phone": "+6398878802928"},
    },
    3: {
        "00-08": {"name": "Dr. Adif Rizal", "phone": "+6342548092021"},
        "08-16": {"name": "Dr. Rayhan", "phone": "+6398878802928"},
        "16-00": {"name": "Dr. Hapid Mizan", "phone": "+6344878029529"},
    },
    4: {
        "00-08": {"name": "Dr. Rayhan", "phone": "+6398878802928"},
        "08-16": {"name": "Dr. Rini Hermi", "phone": "+6342548029777"},
        "16-00": {"name": "Dr. Adif Rizal", "phone": "+6342548092021"},
    },
    5: {
        "00-08": {"name": "Dr. Hapid Mizan", "phone": "+6344878029529"},
        "08-16": {"name": "Dr. Adif Rizal", "phone": "+6342548092021"},
        "16-00": {"name": "Dr. Rayhan", "phone": "+6398878802928"},
    },
    6: {
        "00-08": {"name": "Dr. Rini Hermi", "phone": "+6342548029777"},
        "08-16": {"name": "Dr. Rayhan", "phone": "+6398878802928"},
        "16-00": {"name": "Dr. Hapid Mizan", "phone": "+6344878029529"},
    },
}


BPJS_QUEUE_STATE = {
    "date": None,
    "last_number": 0,
}

MAX_BPJS_QUEUE = 150


def get_today_wib():
    return datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d")


def get_on_duty_doctor():
    now = datetime.now(timezone(timedelta(hours=7)))
    weekday = now.weekday()
    hour = now.hour

    if 0 <= hour < 8:
        shift = "00-08"
        display_shift = "00:00 - 08:00 WIB (12:00 AM - 8:00 AM)"
    elif 8 <= hour < 16:
        shift = "08-16"
        display_shift = "08:00 - 16:00 WIB (8:00 AM - 4:00 PM)"
    else:
        shift = "16-00"
        display_shift = "16:00 - 00:00 WIB (4:00 PM - 12:00 AM)"

    doctor = DOCTOR_SCHEDULE[weekday][shift]

    return {
        "name": doctor["name"],
        "phone": doctor["phone"],
        "shift": display_shift,
    }


def get_bpjs_queue_number():
    today = get_today_wib()

    if BPJS_QUEUE_STATE["date"] != today:
        BPJS_QUEUE_STATE["date"] = today
        BPJS_QUEUE_STATE["last_number"] = 0

    if BPJS_QUEUE_STATE["last_number"] >= MAX_BPJS_QUEUE:
        return None

    BPJS_QUEUE_STATE["last_number"] += 1
    return BPJS_QUEUE_STATE["last_number"]


def waiting_for_registration_choice(history):
    if not history:
        return False
        
    for msg in reversed(history):
        if msg.get("role") != "bot":
            continue

        text = msg.get("text", "").lower()

        return (
            "balas dengan: umum atau bpjs" in text
            or "silakan pilih jalur pendaftaran" in text
        )

    return False

def handle_registration_choice(user_message):
    text = user_message.lower().strip()

    if "bpjs" in text:
        queue_number = get_bpjs_queue_number()

        if queue_number is None:
            return (
                "Mohon maaf, kuota antrian BPJS untuk hari ini sudah penuh.\n\n"
                "Batas antrian BPJS adalah 150 pasien per hari.\n"
                "Silakan datang kembali besok atau gunakan jalur Umum bila ingin langsung mendapatkan dokter dan jadwal praktik."
            )

        return (
            "Pendaftaran BPJS berhasil dibuat.\n\n"
            f"Nomor antrian BPJS Anda: BPJS-{queue_number:03d}\n"
            f"Tanggal: {get_today_wib()}\n"
            "Poli tujuan: Poli Umum\n\n"
            "Silakan datang ke loket BPJS untuk verifikasi berkas sebelum pemeriksaan.\n"
            "Catatan: nomor antrian berlaku untuk hari ini."
        )

    if "umum" in text:
        doctor = get_on_duty_doctor()

        return (
            "Anda memilih jalur Umum.\n\n"
            "Berikut dokter Poli Umum yang sedang bertugas:\n\n"
            f"{doctor['name']}\n"
            f"{doctor['phone']}\n"
            f"Jadwal praktik: {doctor['shift']}\n\n"
            "Silakan menuju pendaftaran umum untuk proses pemeriksaan."
        )

    return (
        "Silakan pilih jalur pendaftaran terlebih dahulu.\n\n"
        "Balas dengan:\n"
        "- umum\n"
        "- bpjs"
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


@app.get("/version")
def version():
    return {
        "app": "R Hospital Backend",
        "version": "dataset-engine-registration-flow-v1",
        "screening_engine": "dataset_rule_based_scoring",
        "registration_flow": "umum_bpjs",
        "bpjs_queue_limit_per_day": MAX_BPJS_QUEUE,
        "ai_provider": "groq-primary-gemini-optional",
        "use_gemini": USE_GEMINI,
        "gemini_model": GEMINI_MODEL,
        "groq_model": GROQ_MODEL,
        "duration_fix": True,
    }


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


@app.post("/ask-doctor")
def ask_doctor(request: dict):
    user_message = request.get("message", "")
    history = request.get("history", [])

    if not user_message.strip():
        return {
            "reply": "Silakan tuliskan pertanyaan kesehatan yang ingin Anda tanyakan kepada Susan."
        }

    system_prompt = (
        "Kamu adalah Susan, seorang asisten kesehatan AI perempuan untuk R Hospital yang memiliki empati kepada manusia. "
        "Jawab dalam bahasa Indonesia yang ramah, jelas, singkat, dan mudah dipahami. "
        "Tugasmu menjawab pertanyaan kesehatan umum, edukasi gejala, menjaga pola makan dan tips hidup sehat, "
        "perawatan awal yang aman, penjelasan obat umum, dan kapan pasien perlu periksa. "
        "Jangan memberikan diagnosis pasti. "
        "Jangan membuat resep obat keras atau antibiotik. "
        "Jawab maksimal 5 poin singkat. "
        "Untuk kondisi keracunan, jangan menyarankan obat resep. Sarankan bilas mulut, minum air sedikit-sedikit bila sadar, "
        "jangan paksa muntah, dan segera ke IGD bila tertelan bahan kimia, sesak, muntah terus, nyeri hebat, atau penurunan kesadaran."
    )

    gemini_error = "Gemini dilewati"

    if USE_GEMINI and GEMINI_API_KEY:
        gemini_contents = [
            {
                "role": "user",
                "parts": [{"text": system_prompt}],
            }
        ]

        for msg in history[-6:]:
            role = msg.get("role")
            text = msg.get("text", "")

            if not text:
                continue

            if text.strip() == user_message.strip():
                continue

            gemini_role = "user" if role == "user" else "model"
            gemini_contents.append(
                {
                    "role": gemini_role,
                    "parts": [{"text": text}],
                }
            )

        gemini_contents.append(
            {
                "role": "user",
                "parts": [{"text": user_message}],
            }
        )

        try:
            gemini_response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
                headers={
                    "x-goog-api-key": GEMINI_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "contents": gemini_contents,
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 500,
                    },
                },
                timeout=10,
            )

            if gemini_response.status_code == 200:
                data = gemini_response.json()
                reply = data["candidates"][0]["content"]["parts"][0]["text"]
                return {
                    "reply": reply
                }

            gemini_error = (
                f"Gemini error {gemini_response.status_code}: "
                f"{gemini_response.text[:200]}"
            )

        except Exception as error:
            gemini_error = f"Gemini exception: {str(error)}"

    if GROQ_API_KEY:
        try:
            groq_messages = [
                {
                    "role": "system",
                    "content": system_prompt,
                }
            ]

            for msg in history[-6:]:
                role = msg.get("role")
                text = msg.get("text", "")

                if not text:
                    continue

                if text.strip() == user_message.strip():
                    continue

                if role == "user":
                    groq_messages.append(
                        {
                            "role": "user",
                            "content": text,
                        }
                    )
                elif role == "bot":
                    groq_messages.append(
                        {
                            "role": "assistant",
                            "content": text,
                        }
                    )

            groq_messages.append(
                {
                    "role": "user",
                    "content": user_message,
                }
            )

            groq_response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": groq_messages,
                    "temperature": 0.3,
                    "max_tokens": 500,
                },
                timeout=20,
            )

            if groq_response.status_code != 200:
                return {
                    "reply": (
                        "Maaf, layanan Tanya Susan sedang tidak bisa diakses. "
                        f"Gemini: {gemini_error}. "
                        f"Groq error {groq_response.status_code}: {groq_response.text[:200]}"
                    )
                }

            data = groq_response.json()
            reply = data["choices"][0]["message"]["content"]

            return {
                "reply": reply
            }

        except Exception as error:
            return {
                "reply": (
                    "Maaf, layanan Tanya Susan sedang gangguan. "
                    f"Gemini: {gemini_error}. "
                    f"Groq exception: {str(error)}"
                )
            }

    return {
        "reply": (
            "Maaf, layanan Tanya Susan sedang tidak bisa diakses. "
            f"Detail: {gemini_error}. Groq API key belum diset."
        )
    }