import os
import sys
import json
import requests
from functools import lru_cache
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
    "http://localhost:5174",
    "http://127.0.0.1:5174",
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

GEMINI_API_KEY=isi_api_key_gemini
GEMINI_MODEL=gemini-2.5-flash
USE_GEMINI=true

# Default false Susan pakai Groq dulu dan tidak pending nunggu Gemini
USE_GEMINI = os.getenv("USE_GEMINI", "false").lower() == "true"

DOCTOR_DATASET_PATH = os.path.join(BASE_DIR, "data", "doctor.json")

BPJS_QUEUE_STATE = {
    "date": None,
    "last_number": 0,
}


@lru_cache(maxsize=1)
def load_doctor_dataset():
    with open(DOCTOR_DATASET_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def get_today_wib():
    return datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d")


def get_shift_info():
    now = datetime.now(timezone(timedelta(hours=7)))
    hour = now.hour

    if 0 <= hour < 8:
        return {
            "code": "00-08",
            "display": "00:00 - 08:00 WIB"
        }

    if 8 <= hour < 16:
        return {
            "code": "08-16",
            "display": "08:00 - 16:00 WIB"
        }

    return {
        "code": "16-00",
        "display": "16:00 - 00:00 WIB"
    }


def get_bpjs_limit():
    dataset = load_doctor_dataset()

    return (
        dataset
        .get("services", {})
        .get("outpatient", {})
        .get("bpjs_daily_limit", 150)
    )


def get_on_duty_doctor():
    dataset = load_doctor_dataset()

    now = datetime.now(timezone(timedelta(hours=7)))
    weekday = str(now.weekday())
    shift = get_shift_info()

    doctor = dataset["doctor_schedule"][weekday][shift["code"]]

    return {
        "name": doctor["name"],
        "phone": doctor["phone"],
        "speciality": doctor.get("speciality", "Dokter Umum"),
        "shift_code": shift["code"],
        "shift": shift["display"],
    }


def get_bpjs_queue_number():
    today = get_today_wib()
    max_bpjs_queue = get_bpjs_limit()

    if BPJS_QUEUE_STATE["date"] != today:
        BPJS_QUEUE_STATE["date"] = today
        BPJS_QUEUE_STATE["last_number"] = 0

    if BPJS_QUEUE_STATE["last_number"] >= max_bpjs_queue:
        return None

    BPJS_QUEUE_STATE["last_number"] += 1
    return BPJS_QUEUE_STATE["last_number"]


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
        "bpjs_queue_limit_per_day": get_bpjs_limit(),
        "doctor_dataset": "doctor.json",
        "service_flow": "online_consultation_or_outpatient",
        "ai_provider": "groq-primary-gemini-optional",
        "use_gemini": USE_GEMINI,
        "gemini_model": GEMINI_MODEL,
        "groq_model": GROQ_MODEL,
        "duration_fix": True,
    }


def get_selected_service(history):
    if not history:
        return None

    for msg in reversed(history):
        if msg.get("role") != "bot":
            continue

        text = msg.get("text", "").lower()

        if "anda memilih konsul online" in text:
            return "online"

        if "anda memilih daftar umum" in text:
            return "umum"

        if "anda memilih bpjs" in text:
            return "bpjs"

    return None


def service_menu_reply():
    return (
        "Silakan pilih layanan terlebih dahulu:\n\n"
        "1. Konsul Online\n"
        "2. Daftar Umum\n"
        "3. BPJS\n\n"
        "Balas dengan angka atau nama layanan."
    )


def handle_initial_service_choice(user_message):
    text = user_message.lower().strip()

    if text in ["1", "konsul", "online", "konsul online"] or "konsul" in text or "online" in text:
        return (
            "Anda memilih Konsul Online.\n\n"
            "Layanan ini hanya tersedia untuk pasien Umum dan tidak menggunakan BPJS.\n\n"
            "Silakan ceritakan keluhan Anda, umur, sudah berapa lama gejalanya, "
            "dan suhu tubuh jika ada demam."
        )

    if text in ["2", "umum", "daftar umum", "rawat jalan umum"] or "umum" in text:
        return (
            "Anda memilih Daftar Umum.\n\n"
            "Silakan ceritakan keluhan Anda, umur, sudah berapa lama gejalanya, "
            "dan suhu tubuh jika ada demam."
        )

    if text in ["3", "bpjs", "daftar bpjs"] or "bpjs" in text:
        return (
            "Anda memilih BPJS.\n\n"
            "Silakan ceritakan keluhan Anda, umur, sudah berapa lama gejalanya, "
            "dan suhu tubuh jika ada demam."
        )

    return service_menu_reply()


def is_screening_result(reply):
    return "Hasil skrining awal R Hospital:" in reply

def extract_poli_from_screening(screening_text):
    for line in screening_text.splitlines():
        if line.lower().startswith("poli rekomendasi:"):
            return line.split(":", 1)[1].strip()

    return "Poli Umum"

def get_speciality_by_poli(recommended_poli):
    poli = (recommended_poli or "").lower()
    if "gigi" in poli:
        return "Dokter Gigi"
    if "tht" in poli:
        return "Dokter THT"
    return "Dokter Umum"


def build_service_result(selected_service, screening_text=""):
    recommended_poli = extract_poli_from_screening(screening_text)
    doctor_speciality = get_speciality_by_poli(recommended_poli)

    if selected_service == "online":
        doctor = get_on_duty_doctor()

        return (
            "Informasi Konsul Online:\n\n"
            "Konsul online hanya tersedia untuk pasien Umum.\n"
            "BPJS tidak berlaku untuk layanan konsul online.\n\n"
            f"Poli tujuan: {recommended_poli}\n"
            f"Dokter: {doctor['name']}\n"
            f"Spesialisasi: {doctor_speciality}\n"
            f"Jam tersedia: {doctor['shift']}\n"
            f"Nomor telepon/WhatsApp: {doctor['phone']}\n\n"
            "Silakan hubungi nomor tersebut untuk melanjutkan konsultasi online."
        )

    if selected_service == "umum":
        doctor = get_on_duty_doctor()

        return (
            "Pendaftaran Daftar Umum berhasil dibuat.\n\n"
            "Berikut jadwal dokter:\n\n"
            f"Poli tujuan: {recommended_poli}\n"
            f"Dokter: {doctor['name']}\n"
            f"Spesialisasi: {doctor_speciality}\n"
            f"Jam tersedia: {doctor['shift']}\n"
            f"Nomor telepon/WhatsApp: {doctor['phone']}\n\n"
            "Silakan datang ke bagian pendaftaran umum sebelum menuju poli pemeriksaan."
        )

    if selected_service == "bpjs":
        queue_number = get_bpjs_queue_number()
        max_bpjs_queue = get_bpjs_limit()

        if queue_number is None:
            return (
                "Mohon maaf, kuota antrian BPJS untuk hari ini sudah penuh.\n\n"
                f"Batas antrian BPJS adalah {max_bpjs_queue} pasien per hari.\n"
                "Silakan datang kembali besok atau gunakan jalur Umum."
            )

        return (
            "Pendaftaran BPJS berhasil dibuat.\n\n"
            f"Nomor antrian BPJS Anda: BPJS-{queue_number:03d}\n"
            f"Tanggal: {get_today_wib()}\n"
            f"Poli tujuan: {recommended_poli}\n\n"
            "Silakan datang ke loket BPJS untuk verifikasi berkas sebelum pemeriksaan.\n"
            "Catatan: nomor antrian berlaku untuk hari ini. Pemanggilan pasien dimulai jam 09:00 WIB."
        )

    return ""


@app.post("/chat")
def chat(request: dict):
    user_message = request.get("message", "")
    history = request.get("history", [])

    selected_service = get_selected_service(history)

    if selected_service is None:
        reply = handle_initial_service_choice(user_message)
        return {"reply": reply}

    reply = screening_reply(
        user_message,
        history,
        on_duty_doctor=get_on_duty_doctor()
    )

    if is_screening_result(reply):
        service_result = build_service_result(selected_service, reply)
        reply = reply + "\n\n" + service_result

    return {"reply": reply}

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
