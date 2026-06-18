import json
import os
import re
from functools import lru_cache

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATASET_PATH = os.path.join(BASE_DIR, "data", "disease_dataset.json")


def merge_user_text(history, current_message):
    texts = []

    if history:
        for msg in history:
            if msg.get("role") == "user":
                value = msg.get("text", "")
                if value:
                    texts.append(value)

    if current_message and current_message not in texts:
        texts.append(current_message)

    return " ".join(texts).lower()


@lru_cache(maxsize=1)
def load_dataset(dataset_path=DEFAULT_DATASET_PATH):
    with open(dataset_path, "r", encoding="utf-8") as file:
        return json.load(file)


def is_negated(text, keyword):
    patterns = [
        rf"(tidak ada|ga ada|gak ada|nggak ada|tanpa)\s+{re.escape(keyword)}",
        rf"(tidak|ga|gak|nggak|enggak)\s+{re.escape(keyword)}",
        rf"{re.escape(keyword)}\s+(tidak ada|ga ada|gak ada|nggak ada)",
    ]

    return any(re.search(pattern, text) for pattern in patterns)


def detect_symptoms(text, dataset=None):
    dataset = dataset or load_dataset()
    symptom_aliases = dataset.get("symptom_aliases", {})
    detected = []

    for symptom, aliases in symptom_aliases.items():
        for alias in aliases:
            if alias in text and not is_negated(text, alias):
                detected.append(symptom)
                break

    return sorted(set(detected))


def detect_age(text):
    text = (text or "").lower().strip()

    patterns = [
        r"(umur|usia)\s*(saya|pasien)?\s*(\d{1,3})",
        r"(saya|pasien)\s*(berumur|berusia)\s*(\d{1,3})",
        r"(\d{1,3})\s*(tahun|thn|th)\s*(umur|usia)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            numbers = re.findall(r"\d{1,3}", match.group(0))
            if numbers:
                age = int(numbers[0])
                if 0 < age <= 120:
                    return age

    standalone_age_patterns = [
        r"(?<!selama\s)(?<!sejak\s)(?<!sudah\s)(?<!sekitar\s)(?<!kurang lebih\s)(\d{1,3})\s*(tahun|thn|th)\b",
    ]

    for pattern in standalone_age_patterns:
        match = re.search(pattern, text)
        if match:
            age = int(match.group(1))
            if 0 < age <= 120:
                return age

    # Jawaban pendek seperti "31"
    if re.fullmatch(r"\d{1,3}", text):
        age = int(text)
        if 0 < age <= 120:
            return age

    return None


def detect_duration_days(text):
    text = (text or "").lower().strip()
    durations = []

    patterns = [
        (r"(\d+)\s*hari", 1),
        (r"(\d+)\s*minggu", 7),
        (r"(\d+)\s*bulan", 30),
        (r"(\d+)\s*jam", 1 / 24),
    ]

    for pattern, multiplier in patterns:
        for match in re.finditer(pattern, text):
            durations.append(int(match.group(1)) * multiplier)

    year_patterns = [
        r"(selama|sejak|sudah|kurang lebih|sekitar)\s*(\d+)\s*tahun",
        r"(\d+)\s*tahun\s*(terakhir|lamanya)",
    ]

    for pattern in year_patterns:
        for match in re.finditer(pattern, text):
            numbers = re.findall(r"\d+", match.group(0))
            if numbers:
                durations.append(int(numbers[0]) * 365)

    if "kemarin" in text:
        durations.append(1)

    if "hari ini" in text or "sejak tadi" in text:
        durations.append(0.5)

    if durations:
        return int(max(durations))

    return None


def detect_temperature(text):
    text = (text or "").lower().strip()

    match = re.search(r"(\d{2}(?:[.,]\d)?)\s*(c|celcius|derajat)", text)
    if match:
        return float(match.group(1).replace(",", "."))

    return None


def detect_negative_info(text):
    text = (text or "").lower().strip()

    negative_patterns = [
        r"\btidak ada\b",
        r"\bga ada\b",
        r"\bgak ada\b",
        r"\bnggak ada\b",
        r"\btanpa\b",
        r"\btidak\b",
        r"\benggak\b",
        r"\bnggak\b",
        r"\bga\b",
        r"\bgak\b",
        r"\bg\b",
    ]

    return any(re.search(pattern, text) for pattern in negative_patterns)

def detect_positive_other_info(text):
    text = (text or "").lower().strip()

    positive_patterns = [
        r"\bada\b",
        r"\bada gejala lain\b",
        r"\bada keluhan lain\b",
    ]

    if detect_negative_info(text):
        return False

    return any(re.search(pattern, text) for pattern in positive_patterns)


def emergency_check(text, symptoms, temperature, dataset=None):
    dataset = dataset or load_dataset()
    reasons = []

    for keyword in dataset.get("global_emergency_keywords", []):
        if keyword in text and not is_negated(text, keyword):
            reasons.append(keyword)

    if temperature and temperature >= 39.5:
        reasons.append("demam sangat tinggi")

    emergency_symptoms = [
        "sesak napas",
        "nyeri dada",
        "batuk darah",
        "kejang",
        "pingsan",
        "lemah separuh badan",
        "sakit kepala hebat",
        "penglihatan buram",
        "urine darah",
        "bab berdarah",
    ]

    for symptom in emergency_symptoms:
        if symptom in symptoms and not is_negated(text, symptom):
            reasons.append(symptom)

    return sorted(set(reasons))


def ask_missing_info(symptoms, age, duration_days, temperature, text):
    missing = []

    if age is None:
        missing.append("umur pasien")

    if duration_days is None:
        missing.append("sudah berapa lama gejalanya")

    if "demam" in symptoms and temperature is None:
        missing.append("suhu tubuh berapa derajat")

    if len(symptoms) <= 1 and not detect_negative_info(text):
        missing.append("apakah ada gejala lain atau tidak ada gejala lain")

    return missing


def classify_diseases(symptoms, duration_days=None, dataset=None, top_n=3):
    dataset = dataset or load_dataset()
    results = []

    for disease in dataset.get("diseases", []):
        score = 0
        matched_main = []
        matched_additional = []
        matched_danger = []

        main_symptoms = disease.get("main_symptoms", [])
        additional_symptoms = disease.get("additional_symptoms", [])
        danger_symptoms = disease.get("danger_symptoms", [])

        for symptom in symptoms:
            if symptom in main_symptoms:
                score += 3
                matched_main.append(symptom)
            elif symptom in additional_symptoms:
                score += 1
                matched_additional.append(symptom)

            if symptom in danger_symptoms:
                score += 5
                matched_danger.append(symptom)

        min_duration = disease.get("min_duration_days", 0)

        if duration_days is not None and duration_days >= min_duration:
            score += 1

        if duration_days is not None and min_duration > 0 and duration_days < min_duration:
            score -= 2

        if score <= 0:
            continue

        max_possible_score = (
            (len(main_symptoms) * 3)
            + len(additional_symptoms)
            + (len(danger_symptoms) * 5)
            + 1
        )

        match_percent = round((score / max_possible_score) * 100, 1) if max_possible_score else 0

        results.append({
            "code": disease.get("code"),
            "name": disease.get("name"),
            "category": disease.get("category"),
            "level": disease.get("level"),
            "score": score,
            "match_percent": match_percent,
            "matched_main": matched_main,
            "matched_additional": matched_additional,
            "matched_danger": matched_danger,
            "explanation": disease.get("explanation"),
            "advice": disease.get("advice"),
            "doctor_recommended_after_days": disease.get("doctor_recommended_after_days", 2),
        })

    results.sort(key=lambda item: (item["score"], item["match_percent"]), reverse=True)

    return results[:top_n]


def get_basic_care_advice(symptoms):
    advice = []

    if "demam" in symptoms or "sakit kepala" in symptoms or "nyeri otot" in symptoms:
        advice.append(
            "- Untuk demam/nyeri: gunakan obat bebas seperti paracetamol sesuai aturan pakai pada kemasan bila tidak ada alergi/kontraindikasi."
        )

    if "batuk" in symptoms:
        advice.append(
            "- Untuk batuk: perbanyak minum air hangat, hindari asap/debu, dan gunakan masker."
        )

    if "pilek" in symptoms or "hidung tersumbat" in symptoms:
        advice.append(
            "- Untuk pilek/hidung tersumbat: istirahat cukup dan minum hangat."
        )

    if "diare" in symptoms or "muntah" in symptoms:
        advice.append(
            "- Untuk diare/muntah: utamakan cairan oralit/cairan elektrolit untuk mencegah dehidrasi."
        )

    if "nyeri ulu hati" in symptoms or "perut kembung" in symptoms:
        advice.append(
            "- Untuk keluhan lambung: makan porsi kecil tapi sering, hindari kopi, pedas, asam, dan jangan langsung rebahan setelah makan."
        )

    if not advice:
        advice.append(
            "- Istirahat cukup, minum air yang cukup, makan teratur, dan pantau perkembangan gejala."
        )

    advice.append(
        "- Jika muncul tanda bahaya seperti sesak, nyeri dada, pingsan, kejang, batuk darah, atau kondisi memburuk, segera ke IGD."
    )

    return "\n".join(advice)


def recommend_poli(top, symptoms):
    name = (top.get("name") or "").lower()
    category = (top.get("category") or "").lower()
    symptom_text = " ".join(symptoms).lower()

    dental_keywords = [
        "gigi",
        "gusi",
        "mulut",
        "sariawan",
        "rahang",
    ]

    tht_keywords = [
        "telinga",
        "hidung",
        "tenggorokan",
        "pilek",
        "hidung tersumbat",
        "sinus",
        "amandel",
        "ispa",
        "common cold",
        "batuk pilek",
        "flu",
        "batuk",
    ]

    if any(keyword in name or keyword in category or keyword in symptom_text for keyword in dental_keywords):
        return "Poli Gigi"

    if any(keyword in name or keyword in category or keyword in symptom_text for keyword in tht_keywords):
        return "Poli THT"

    return "Poli Umum"

    
def format_screening_reply(
    symptoms,
    age,
    duration_days,
    temperature,
    emergency_reasons,
    results,
    on_duty_doctor=None,
):
    if emergency_reasons:
        return (
            "Tanda bahaya terdeteksi.\n\n"
            f"Alasan: {', '.join(emergency_reasons)}.\n\n"
            "Kondisi ini termasuk urgent. Sebaiknya segera ke IGD atau fasilitas kesehatan terdekat.\n\n"
            "Catatan: chatbot ini hanya membantu skrining awal dan bukan pengganti diagnosis dokter."
        )

    if not results:
        return (
            "Saya menangkap gejala: " + ", ".join(symptoms) + ".\n\n"
            "Namun gejala belum cukup spesifik untuk dicocokkan ke dataset penyakit. "
            "Silakan lengkapi keluhan lain seperti durasi, suhu, dan gejala penyerta."
        )

    top = results[0]
    recommended_poli = recommend_poli(top, symptoms)

    lines = [
        "Hasil skrining awal R Hospital:",
        "",
        f"Gejala terdeteksi: {', '.join(symptoms)}.",
        f"Umur: {age} tahun." if age is not None else "Umur: belum diisi.",
        f"Durasi: sekitar {duration_days} hari." if duration_days is not None else "Durasi: belum diisi.",
        f"Suhu: {temperature}°C." if temperature is not None else "Suhu: belum diisi.",
        "",
        f"Kemungkinan tertinggi: {top['name']}",
        f"Kategori: {top['category']}",
        f"Tingkat perhatian: {top['level']}",
        f"Poli rekomendasi: {recommended_poli}",
        "",
        f"Penjelasan: {top['explanation']}",
    ]

    if top.get("advice"):
        lines.extend([
            "",
            f"Saran awal: {top['advice']}",
        ])

    if len(results) > 1:
        lines.extend(["", "Kemungkinan lain:"])

        for item in results[1:]:
            lines.append(f"- {item['name']}")

    if duration_days is not None and duration_days <= 1:
        lines.extend([
            "",
            "Perawatan awal:",
            get_basic_care_advice(symptoms),
        ])

    lines.extend([
        "",
        "Catatan: ini bukan diagnosis pasti. Diagnosis tetap memerlukan pemeriksaan langsung oleh tenaga medis.",
    ])

    lines = [str(line) for line in lines if line is not None]

    return "\n".join(lines)

def screening_reply(message, history=None, on_duty_doctor=None):
    dataset = load_dataset()

    current_text = (message or "").lower().strip()
    text = merge_user_text(history or [], message)

    symptoms = detect_symptoms(text, dataset)
    current_symptoms = detect_symptoms(current_text, dataset)

    age = detect_age(text)
    if age is None:
        age = detect_age(current_text)

    duration_days = detect_duration_days(text)
    if duration_days is None:
        duration_days = detect_duration_days(current_text)

    temperature = detect_temperature(text)
    if temperature is None:
        temperature = detect_temperature(current_text)

    if detect_positive_other_info(current_text) and not current_symptoms:
        return (
            "Baik, gejala tambahannya apa?\n\n"
            "Contohnya: demam, pilek, batuk, sakit tenggorokan, sesak napas, "
            "nyeri dada, mual, muntah, diare, nyeri perut, sakit gigi, "
            "nyeri telinga, atau sakit kepala."
        )

    if not symptoms:
        return (
            "Saya belum menangkap gejala yang cukup jelas.\n\n"
            "Silakan tuliskan keluhan utama Anda, umur, sudah berapa lama gejalanya, "
            "dan suhu tubuh jika ada demam.\n\n"
            "Contoh: saya batuk pilek 2 hari umur 19 tahun."
        )

    emergency_reasons = emergency_check(text, symptoms, temperature, dataset)

    if emergency_reasons:
        return format_screening_reply(
            symptoms=symptoms,
            age=age,
            duration_days=duration_days,
            temperature=temperature,
            emergency_reasons=emergency_reasons,
            results=[],
            on_duty_doctor=on_duty_doctor,
        )

    missing = ask_missing_info(symptoms, age, duration_days, temperature, text)

    if missing:
        return (
            "Saya menangkap gejala: " + ", ".join(symptoms) + ".\n\n"
            "Supaya skrining lebih akurat, mohon lengkapi:\n"
            + "\n".join([f"- {item}" for item in missing])
        )

    results = classify_diseases(
        symptoms=symptoms,
        duration_days=duration_days,
        dataset=dataset,
        top_n=3,
    )

    return format_screening_reply(
        symptoms=symptoms,
        age=age,
        duration_days=duration_days,
        temperature=temperature,
        emergency_reasons=[],
        results=results,
        on_duty_doctor=on_duty_doctor,
    )