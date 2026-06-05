import re
import json
from pathlib import Path


def load_diseases():
    file_path = Path(__file__).parent / "data" / "penyakit.json"

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


DISEASE_RULES = load_diseases()


EMERGENCY_KEYWORDS = [
    "sesak berat",
    "sulit bernapas",
    "napas berat",
    "nyeri dada",
    "dada terasa tertekan",
    "pingsan",
    "kejang",
    "bingung",
    "tidak sadar",
    "bibir biru",
    "muntah darah",
    "bab berdarah",
    "perdarahan hebat",
    "lemas sekali",
    "nyeri perut hebat",
    "muntah terus",
    "dehidrasi berat",
]


SYMPTOM_KEYWORDS = {
    "demam": ["demam", "panas", "meriang", "suhu tinggi"],
    "batuk": ["batuk"],
    "pilek": ["pilek", "hidung meler", "bersin"],
    "sakit_tenggorokan": ["sakit tenggorokan", "tenggorokan sakit", "nyeri menelan"],
    "sesak": ["sesak", "sulit bernapas", "napas berat"],
    "sakit_kepala": ["sakit kepala", "pusing", "kepala nyeri"],
    "mual": ["mual"],
    "muntah": ["muntah"],
    "diare": ["diare", "mencret"],
    "nyeri_perut": ["sakit perut", "nyeri perut", "perut sakit"],
    "ruam": ["ruam", "bintik merah", "bercak merah"],
    "nyeri_otot": ["nyeri otot", "badan sakit", "pegal", "linu"],
    "nyeri_dada": ["nyeri dada", "dada sakit", "dada sesak"],
    "gatal": ["gatal"],
    "lemas": ["lemas", "lelah", "tidak bertenaga"],
}


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def no_extra_symptoms_answer(text: str) -> bool:
    no_keywords = [
        "tidak",
        "tidak ada",
        "tidak ada gejala lain",
        "tidak ada keluhan lain",
        "ga",
        "gak",
        "ga ada",
        "gak ada",
        "nggak",
        "nggak ada",
        "enggak",
        "enggak ada",
        "tidak terdapat",
    ]

    return any(keyword in text for keyword in no_keywords)


def ada_emergency(text: str) -> bool:
    return contains_any(text, EMERGENCY_KEYWORDS)


def extract_symptoms(text: str) -> list[str]:
    found = []

    for symptom, keywords in SYMPTOM_KEYWORDS.items():
        if contains_any(text, keywords):
            found.append(symptom)

    return found


def extract_duration(text: str):
    patterns = [
        r"(\d+)\s*hari",
        r"(\d+)\s*minggu",
        r"(\d+)\s*jam",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)

    if "kemarin" in text:
        return "1 hari"

    return None


def extract_temperature(text: str):
    match = re.search(r"(\d{2}(?:[.,]\d)?)\s*(?:derajat|c|celcius)", text)

    if match:
        return match.group(1).replace(",", ".")

    return None


def extract_age(text: str):
    match = re.search(r"umur\s*(\d+)|usia\s*(\d+)|(\d+)\s*tahun", text)

    if match:
        return next(group for group in match.groups() if group)

    return None


def missing_required_info(text: str, symptoms: list[str], latest_text: str = "") -> list[str]:
    missing = []

    if not extract_age(text):
        missing.append("umur/usia")

    if not extract_duration(text):
        missing.append("durasi gejala")

    if "demam" in symptoms and not extract_temperature(text):
        missing.append("suhu tubuh")

    user_sudah_jawab_tidak = (
        no_extra_symptoms_answer(text)
        or no_extra_symptoms_answer(latest_text)
    )

    if len(symptoms) < 2 and not user_sudah_jawab_tidak:
        missing.append("gejala lain yang menyertai")

    return missing


def score_diseases(symptoms: list[str]) -> list[dict]:
    results = []

    for rule in DISEASE_RULES:
        matched = list(set(symptoms) & set(rule["symptoms"]))
        score = len(matched)

        if score > 0:
            results.append({
                "name": rule["name"],
                "matched": matched,
                "score": score,
                "explanation": rule.get("explanation", "Belum ada penjelasan pada dataset."),
                "advice": rule.get("advice", "Silakan konsultasi ke dokter untuk evaluasi lebih lanjut."),
                "danger_signs": rule.get("danger_signs", []),
            })

    results.sort(key=lambda item: item["score"], reverse=True)

    return results


def build_followup_question(missing: list[str], symptoms: list[str]) -> str:
    questions = []

    if "umur/usia" in missing:
        questions.append("umur pasien berapa?")

    if "durasi gejala" in missing:
        questions.append("gejalanya sudah berapa lama?")

    if "suhu tubuh" in missing:
        questions.append("suhu tubuhnya berapa derajat?")

    if "gejala lain yang menyertai" in missing:
        known_symptoms = ", ".join(symptoms)

        pilihan_gejala = [
            "batuk",
            "pilek",
            "mual",
            "muntah",
            "diare",
            "ruam",
            "nyeri dada",
            "sesak",
            "sakit kepala",
            "nyeri otot",
        ]

        pilihan_gejala = [
            gejala for gejala in pilihan_gejala
            if gejala not in known_symptoms
        ]

        questions.append(
            f"saya sudah menangkap gejala: {known_symptoms}. "
            f"Ada gejala lain seperti {', '.join(pilihan_gejala)}, atau tidak ada gejala lain?"
        )

    return "Boleh lengkapi dulu: " + " ".join(questions)


def medical_agent(user_message: str, history: list | None = None) -> str:
    history = history or []

    combined_text = ""

    for item in history:
        if hasattr(item, "role") and hasattr(item, "text"):
            if item.role == "user":
                combined_text += " " + item.text

        elif isinstance(item, dict):
            if item.get("role") == "user":
                combined_text += " " + item.get("text", "")

    combined_text += " " + user_message

    text = normalize_text(combined_text)
    latest_text = normalize_text(user_message)

    if ada_emergency(text):
        return (
            "Gejala yang Anda sebutkan termasuk tanda bahaya.\n\n"
            "Sebaiknya segera ke IGD atau hubungi layanan medis terdekat.\n\n"
            "Saya tidak bisa memastikan diagnosis dari chat, tetapi gejala seperti ini perlu penanganan langsung."
        )

    symptoms = extract_symptoms(text)

    if not symptoms:
        return (
            "Saya belum menangkap gejala spesifik. "
            "Boleh jelaskan keluhan utama seperti batuk, demam, pilek, mual, muntah, diare, ruam, nyeri dada, atau sesak?"
        )

    missing = missing_required_info(
        text=text,
        symptoms=symptoms,
        latest_text=latest_text,
    )

    if missing:
        return build_followup_question(missing, symptoms)

    disease_results = score_diseases(symptoms)

    if not disease_results:
        return (
            "Gejala sudah saya terima, tetapi belum cukup cocok dengan pola yang ada di dataset sederhana ini.\n\n"
            "Sebaiknya konsultasi ke dokter untuk evaluasi lebih lanjut."
        )

    top_results = disease_results[:3]

    response = "Hasil analisis awal NM Hospital:\n\n"

    for index, item in enumerate(top_results, start=1):
        matched_text = ", ".join(item["matched"])
        danger_text = ", ".join(item["danger_signs"]) if item["danger_signs"] else "-"

        response += f"{index}. Kemungkinan: {item['name']}\n\n"
        response += "Penjelasan:\n"
        response += f"{item['explanation']}\n\n"
        response += "Kenapa kemungkinan ini muncul:\n"
        response += f"Karena pasien menyebutkan gejala yang cocok: {matched_text}.\n\n"
        response += "Saran awal:\n"
        response += f"{item['advice']}\n\n"
        response += "Tanda bahaya yang perlu diperhatikan:\n"
        response += f"{danger_text}\n\n"

    response += (
        "Catatan penting: hasil ini bukan diagnosis pasti. "
        "Diagnosis tetap membutuhkan pemeriksaan langsung oleh tenaga medis."
    )

    return response