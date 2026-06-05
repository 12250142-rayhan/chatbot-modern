from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://chatbot-modern-eight.vercel.app",
        "https://chatbot-modern.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "R Hospital Backend is running"}


@app.get("/test")
def test():
    return {"status": "ok"}


def get_all_user_text(history, current_message):
    texts = []

    if history:
        for msg in history:
            if msg.get("role") == "user":
                texts.append(msg.get("text", ""))

    texts.append(current_message)
    return " ".join(texts).lower()


def detect_symptoms(text):
    symptoms = []

    symptom_map = {
        "demam": ["demam", "panas", "meriang"],
        "batuk": ["batuk"],
        "pilek": ["pilek", "hidung meler", "bersin"],
        "sakit tenggorokan": ["sakit tenggorokan", "tenggorokan sakit", "nyeri menelan"],
        "mual": ["mual"],
        "muntah": ["muntah"],
        "diare": ["diare", "mencret"],
        "sesak": ["sesak", "sulit bernapas", "napas berat"],
        "nyeri dada": ["nyeri dada", "dada sakit"],
        "sakit kepala": ["sakit kepala", "pusing"],
        "ruam": ["ruam", "bintik merah", "gatal"],
    }

    for symptom, keywords in symptom_map.items():
        if any(keyword in text for keyword in keywords):
            symptoms.append(symptom)

    return symptoms


def has_age(text):
    return "tahun" in text or "umur" in text or "usia" in text


def has_duration(text):
    return (
        "hari" in text
        or "minggu" in text
        or "jam" in text
        or "kemarin" in text
        or "sejak" in text
    )


def has_no_extra_symptom(text):
    no_words = [
        "tidak ada",
        "ga ada",
        "gak ada",
        "nggak ada",
        "tidak",
        "enggak",
        "nggak",
        "ga",
        "gak",
    ]
    return any(word in text for word in no_words)


def has_emergency(text):
    emergency_words = [
        "sesak berat",
        "sulit bernapas",
        "nyeri dada",
        "pingsan",
        "kejang",
        "tidak sadar",
        "muntah darah",
        "bibir biru",
    ]
    return any(word in text for word in emergency_words)


def medical_reply(message, history):
    text = get_all_user_text(history, message)
    latest_text = message.lower()

    if has_emergency(text):
        return (
            "Gejala yang Anda sebutkan termasuk tanda bahaya.\n\n"
            "Sebaiknya segera ke IGD atau hubungi tenaga medis terdekat. "
            "Chatbot ini tidak bisa memastikan diagnosis, tetapi gejala seperti sesak berat, nyeri dada, pingsan, atau kejang perlu penanganan langsung."
        )

    symptoms = detect_symptoms(text)

    if not symptoms:
        return (
            "Boleh jelaskan keluhan utama Anda? Contohnya demam, batuk, pilek, mual, muntah, diare, sakit tenggorokan, sesak, atau nyeri dada."
        )

    missing = []

    if not has_age(text):
        missing.append("umur pasien")

    if not has_duration(text):
        missing.append("sudah berapa lama gejalanya")

    if len(symptoms) < 2 and not has_no_extra_symptom(latest_text):
        missing.append("apakah ada gejala lain atau tidak ada gejala lain")

    if missing:
        symptom_text = ", ".join(symptoms)
        return (
            f"Saya menangkap gejala: {symptom_text}.\n\n"
            f"Boleh lengkapi dulu: {', '.join(missing)}?"
        )

    symptom_set = set(symptoms)

    if "demam" in symptom_set and "batuk" in symptom_set:
        kemungkinan = "infeksi saluran napas atas, flu, atau infeksi virus ringan"
        penjelasan = (
            "Demam disertai batuk sering berhubungan dengan infeksi saluran pernapasan. "
            "Biasanya dapat disebabkan oleh virus, tetapi tetap perlu diperhatikan bila gejala memburuk."
        )
        saran = (
            "Istirahat cukup, minum air yang cukup, gunakan masker, dan pantau suhu tubuh. "
            "Segera periksa jika demam tinggi lebih dari 3 hari, sesak, nyeri dada, atau kondisi makin lemah."
        )

    elif "batuk" in symptom_set and "pilek" in symptom_set:
        kemungkinan = "common cold / batuk pilek"
        penjelasan = (
            "Batuk dan pilek sering terjadi karena iritasi atau infeksi virus ringan pada saluran napas atas."
        )
        saran = (
            "Cukup istirahat, minum air hangat, hindari asap rokok/debu, dan gunakan masker. "
            "Periksa ke dokter bila batuk lebih dari 2 minggu, sesak, atau dahak berdarah."
        )

    elif "demam" in symptom_set:
        kemungkinan = "demam akibat infeksi ringan atau kondisi tubuh sedang melawan infeksi"
        penjelasan = (
            "Demam adalah tanda tubuh sedang merespons infeksi atau peradangan. Penyebabnya bisa ringan sampai serius, tergantung gejala lain."
        )
        saran = (
            "Pantau suhu tubuh, cukup minum, dan istirahat. "
            "Periksa jika suhu sangat tinggi, demam lebih dari 3 hari, muncul ruam, sesak, nyeri hebat, atau lemas berat."
        )

    elif "batuk" in symptom_set:
        kemungkinan = "batuk ringan, iritasi tenggorokan, alergi, atau infeksi saluran napas atas"
        penjelasan = (
            "Batuk bisa muncul karena iritasi, alergi, atau infeksi ringan. Jika tanpa demam dan sesak, biasanya tidak darurat."
        )
        saran = (
            "Minum air hangat, hindari debu/asap, dan istirahat. "
            "Periksa bila batuk lebih dari 2 minggu, sesak, nyeri dada, demam tinggi, atau dahak berdarah."
        )

    elif "diare" in symptom_set or "muntah" in symptom_set or "mual" in symptom_set:
        kemungkinan = "gangguan pencernaan atau gastroenteritis ringan"
        penjelasan = (
            "Mual, muntah, atau diare dapat terjadi karena gangguan pencernaan, makanan yang tidak cocok, atau infeksi saluran cerna."
        )
        saran = (
            "Minum cukup cairan, makan makanan ringan, dan hindari makanan pedas/berminyak. "
            "Segera periksa jika ada tanda dehidrasi, muntah terus, BAB berdarah, atau nyeri perut hebat."
        )

    else:
        kemungkinan = "keluhan ringan yang perlu dipantau"
        penjelasan = (
            "Gejala yang disebutkan belum cukup spesifik untuk mengarah ke satu kemungkinan penyakit tertentu."
        )
        saran = (
            "Pantau gejala, istirahat, dan konsultasikan ke dokter jika gejala memburuk atau tidak membaik."
        )

    return (
        "Hasil analisis awal R Hospital:\n\n"
        f"Kemungkinan: {kemungkinan}.\n\n"
        f"Penjelasan:\n{penjelasan}\n\n"
        f"Saran awal:\n{saran}\n\n"
        "Catatan: ini bukan diagnosis pasti. Diagnosis tetap perlu pemeriksaan langsung oleh tenaga medis."
    )


@app.post("/chat")
def chat(request: dict):
    user_message = request.get("message", "")
    history = request.get("history", [])

    reply = medical_reply(user_message, history)

    return {"reply": reply}