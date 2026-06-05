import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/")
def home():
    return {"message": "R Hospital Backend is running"}


@app.get("/test")
def test():
    return {"status": "ok"}


def merge_user_text(history, current_message):
    texts = []

    if history:
        for msg in history:
            if msg.get("role") == "user":
                texts.append(msg.get("text", ""))

    texts.append(current_message)
    return " ".join(texts).lower()


def detect_age(text):
    match = re.search(r"(\d{1,3})\s*(tahun|thn|th|yo|y/o)", text)
    if match:
        return int(match.group(1))

    match = re.search(r"(umur|usia)\s*(saya)?\s*(\d{1,3})", text)
    if match:
        return int(match.group(3))

    return None


def detect_duration_days(text):
    patterns = [
        (r"(\d+)\s*hari", 1),
        (r"(\d+)\s*minggu", 7),
        (r"(\d+)\s*bulan", 30),
        (r"(\d+)\s*tahun", 365),
        (r"(\d+)\s*jam", 1 / 24),
    ]

    durations = []

    for pattern, multiplier in patterns:
        for match in re.finditer(pattern, text):
            durations.append(int(match.group(1)) * multiplier)

    if "kemarin" in text:
        durations.append(1)

    if "hari ini" in text or "sejak tadi" in text:
        durations.append(0.5)

    if durations:
        return int(max(durations))

    return None


def detect_temperature(text):
    match = re.search(r"(\d{2}(?:[.,]\d)?)\s*(c|celcius|derajat)", text)
    if match:
        return float(match.group(1).replace(",", "."))
    return None


def contains_any(text, keywords):
    return any(keyword in text for keyword in keywords)


def detect_symptoms(text):
    symptom_map = {
        # respirasi
        "batuk": ["batuk"],
        "pilek": ["pilek", "hidung meler", "ingusan", "bersin"],
        "sakit tenggorokan": ["sakit tenggorokan", "tenggorokan sakit", "nyeri menelan"],
        "sesak napas": ["sesak", "sesak napas", "sulit bernapas", "napas berat"],
        "nyeri dada": ["nyeri dada", "dada sakit", "dada terasa berat"],
        "dahak": ["dahak", "berdahak"],
        "dahak darah": ["batuk darah", "dahak darah", "darah saat batuk"],
        "keringat malam": ["keringat malam"],
        "berat badan turun": ["berat badan turun", "bb turun", "kurus"],

        # demam umum
        "demam": ["demam", "panas", "meriang", "menggigil"],
        "sakit kepala": ["sakit kepala", "pusing"],
        "nyeri otot": ["nyeri otot", "badan pegal", "pegal"],
        "lemas": ["lemas", "lemah", "tidak bertenaga"],

        # pencernaan
        "mual": ["mual"],
        "muntah": ["muntah"],
        "diare": ["diare", "mencret", "bab cair"],
        "nyeri perut": ["nyeri perut", "sakit perut", "perut sakit"],
        "perut kembung": ["kembung", "begah"],
        "nyeri ulu hati": ["ulu hati", "maag", "asam lambung", "gerd", "dada panas"],

        # kulit
        "ruam": ["ruam", "bintik merah", "kemerahan"],
        "gatal": ["gatal", "gatal-gatal"],
        "bentol": ["bentol", "biduran"],
        "luka bernanah": ["bernanah", "nanah", "luka busuk"],

        # kemih
        "nyeri kencing": ["nyeri kencing", "sakit saat kencing", "anyang-anyangan", "kencing sakit"],
        "sering kencing": ["sering kencing", "bolak balik kencing"],
        "urine darah": ["kencing darah", "urine darah", "air kencing berdarah"],

        # mata
        "mata merah": ["mata merah", "merah pada mata"],
        "mata nyeri": ["mata nyeri", "sakit mata"],
        "penglihatan buram": ["penglihatan buram", "pandangan kabur", "mata kabur"],

        # telinga / THT
        "nyeri telinga": ["sakit telinga", "nyeri telinga", "telinga sakit"],
        "keluar cairan telinga": ["telinga keluar cairan", "cairan dari telinga", "telinga bernanah"],
        "hidung tersumbat": ["hidung tersumbat", "mampet"],

        # gigi
        "sakit gigi": ["sakit gigi", "gigi sakit", "nyeri gigi"],
        "gusi bengkak": ["gusi bengkak", "bengkak gusi"],

        # saraf / neurologis
        "lemah separuh badan": ["lemah separuh badan", "wajah mencong", "pelo", "bicara pelo"],
        "kejang": ["kejang"],
        "pingsan": ["pingsan", "tidak sadar"],
        "sakit kepala hebat": ["sakit kepala hebat", "kepala sangat sakit"],

        # muskuloskeletal
        "nyeri sendi": ["nyeri sendi", "sendi sakit"],
        "bengkak sendi": ["sendi bengkak", "bengkak sendi"],
        "nyeri punggung": ["sakit punggung", "nyeri punggung", "pinggang sakit"],

        # reproduksi sederhana
        "nyeri haid": ["nyeri haid", "haid sakit", "kram haid"],
        "haid tidak teratur": ["haid tidak teratur", "menstruasi tidak teratur", "telat haid"],
        "keputihan": ["keputihan"],
    }

    symptoms = []

    for symptom, keywords in symptom_map.items():
        if contains_any(text, keywords):
            symptoms.append(symptom)

    return symptoms


def detect_negative_info(text):
    negative_words = [
        "tidak ada",
        "ga ada",
        "gak ada",
        "nggak ada",
        "tanpa",
        "tidak",
        "enggak",
        "nggak",
        "ga",
        "gak",
    ]
    return any(word in text for word in negative_words)


def emergency_check(text, symptoms, temperature):
    reasons = []

    emergency_symptoms = {
        "sesak napas": "sesak napas",
        "nyeri dada": "nyeri dada",
        "dahak darah": "batuk atau dahak berdarah",
        "kejang": "kejang",
        "pingsan": "pingsan/tidak sadar",
        "lemah separuh badan": "gejala mirip stroke",
        "sakit kepala hebat": "sakit kepala hebat",
        "penglihatan buram": "gangguan penglihatan",
        "urine darah": "urine berdarah",
    }

    for symptom, label in emergency_symptoms.items():
        if symptom in symptoms:
            reasons.append(label)

    if temperature and temperature >= 39.5:
        reasons.append("demam sangat tinggi")

    danger_keywords = [
        "bibir biru",
        "sangat lemas",
        "sulit bangun",
        "dehidrasi berat",
        "muntah terus",
        "bab berdarah",
        "mimisan terus",
        "nyeri perut hebat",
        "perut keras",
    ]

    for keyword in danger_keywords:
        if keyword in text:
            reasons.append(keyword)

    return reasons


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


def make_result(level, kemungkinan, penjelasan, saran):
    return {
        "level": level,
        "kemungkinan": kemungkinan,
        "penjelasan": penjelasan,
        "saran": saran,
    }


def analyze_respiratory(symptoms, duration_days, temperature):
    if "batuk" in symptoms:
        if duration_days is not None and duration_days >= 56:
            return make_result(
                "tinggi",
                "batuk kronis. Perlu dipikirkan TB paru, asma, alergi, GERD/asam lambung, bronkitis kronis, atau infeksi paru yang belum sembuh",
                f"Batuk sekitar {duration_days} hari sudah termasuk batuk lama/kronis, bukan batuk ringan biasa. Durasi ini perlu evaluasi langsung, terutama untuk menyingkirkan TB paru atau penyakit paru lain.",
                "Sebaiknya periksa ke dokter/puskesmas. Pemeriksaan yang mungkin diperlukan: pemeriksaan dahak, rontgen dada, atau evaluasi paru. Gunakan masker dan jangan menunda pemeriksaan."
            )

        if duration_days is not None and duration_days >= 21:
            return make_result(
                "sedang-tinggi",
                "batuk lama/subakut. Bisa karena infeksi yang belum pulih, alergi, asma, GERD, atau kemungkinan TB bila ada gejala penyerta",
                f"Batuk selama {duration_days} hari sudah melewati batuk akut biasa. Bila lebih dari 3 minggu, sebaiknya dievaluasi bila tidak membaik.",
                "Periksa bila batuk tidak membaik, ada demam, dahak kental, berat badan turun, keringat malam, sesak, nyeri dada, atau batuk darah."
            )

        if "demam" in symptoms:
            return make_result(
                "sedang",
                "infeksi saluran napas atas, flu, COVID-like illness, atau infeksi virus/bakteri ringan",
                "Batuk disertai demam sering berkaitan dengan infeksi saluran napas. Biasanya bisa karena virus, tetapi tetap perlu dipantau bila memburuk.",
                "Istirahat, cukup cairan, gunakan masker, dan pantau suhu. Periksa bila demam tinggi lebih dari 3 hari, sesak, nyeri dada, atau kondisi makin lemah."
            )

        if "pilek" in symptoms or "sakit tenggorokan" in symptoms:
            return make_result(
                "ringan-sedang",
                "common cold/batuk pilek, radang tenggorokan ringan, atau iritasi saluran napas",
                "Batuk, pilek, dan sakit tenggorokan sering terjadi karena infeksi virus ringan atau iritasi.",
                "Minum hangat, istirahat, hindari asap/debu. Periksa bila lebih dari 2 minggu, demam tinggi, sesak, atau dahak berdarah."
            )

        return make_result(
            "ringan",
            "batuk akut ringan, iritasi tenggorokan, alergi, atau infeksi saluran napas atas",
            "Batuk durasi pendek sering disebabkan iritasi, alergi, atau infeksi virus ringan. Jika tanpa sesak dan nyeri dada biasanya tidak darurat.",
            "Minum air hangat, hindari asap/debu, cukup istirahat, dan pantau. Periksa bila batuk lebih dari 2 minggu atau muncul tanda bahaya."
        )

    if "pilek" in symptoms or "hidung tersumbat" in symptoms:
        return make_result(
            "ringan",
            "pilek/common cold, rhinitis alergi, atau sinus ringan",
            "Pilek dan hidung tersumbat sering terjadi akibat infeksi virus ringan atau alergi.",
            "Cukup cairan, istirahat, hindari debu/asap. Periksa bila disertai demam tinggi, nyeri wajah berat, atau lebih dari 10 hari tidak membaik."
        )

    if "sakit tenggorokan" in symptoms:
        return make_result(
            "ringan-sedang",
            "radang tenggorokan karena virus, iritasi, atau infeksi bakteri",
            "Sakit tenggorokan bisa terjadi karena virus, iritasi, atau infeksi bakteri. Perlu dilihat apakah ada demam tinggi, sulit menelan, atau pembengkakan.",
            "Minum hangat, istirahat, hindari rokok. Periksa bila nyeri berat, sulit menelan, demam tinggi, atau lebih dari 3–5 hari."
        )

    return None


def analyze_fever(symptoms, duration_days, temperature):
    if temperature and temperature >= 39.5:
        return make_result(
            "tinggi",
            "demam tinggi akibat infeksi yang perlu evaluasi",
            "Suhu tubuh sangat tinggi perlu dipantau serius karena dapat menyebabkan lemas dan dehidrasi.",
            "Periksa ke dokter, terutama bila demam tidak turun, lemas berat, ruam, sesak, muntah terus, atau nyeri kepala hebat."
        )

    if duration_days is not None and duration_days >= 3:
        if "ruam" in symptoms or "nyeri otot" in symptoms or "sakit kepala" in symptoms:
            return make_result(
                "sedang-tinggi",
                "infeksi virus seperti dengue/DBD perlu dipertimbangkan, terutama bila demam tinggi beberapa hari disertai nyeri badan, sakit kepala, ruam, atau lemas",
                f"Demam selama {duration_days} hari disertai gejala penyerta perlu dipantau lebih serius.",
                "Sebaiknya periksa ke fasilitas kesehatan untuk evaluasi. Segera periksa bila muncul mimisan, gusi berdarah, nyeri perut hebat, muntah terus, lemas berat, atau tangan/kaki dingin."
            )

        return make_result(
            "sedang",
            "infeksi virus atau bakteri yang perlu dipantau",
            f"Demam selama {duration_days} hari perlu perhatian, terutama bila tidak membaik.",
            "Cukup minum, istirahat, pantau suhu, dan periksa bila demam lebih dari 3 hari atau memburuk."
        )

    return make_result(
        "ringan-sedang",
        "demam akibat infeksi ringan atau respons tubuh melawan infeksi",
        "Demam adalah tanda tubuh sedang merespons infeksi atau peradangan.",
        "Istirahat, cukup minum, pantau suhu tubuh, dan periksa bila suhu tinggi atau muncul tanda bahaya."
    )


def analyze_digestive(symptoms, duration_days):
    if "nyeri ulu hati" in symptoms or "perut kembung" in symptoms:
        return make_result(
            "ringan-sedang",
            "maag/dispepsia, GERD/asam lambung, atau iritasi lambung",
            "Keluhan ulu hati, kembung, begah, atau dada terasa panas sering berkaitan dengan gangguan lambung atau asam lambung.",
            "Makan teratur, hindari pedas/asam/kopi, jangan langsung rebahan setelah makan. Periksa bila nyeri berat, muntah darah, BAB hitam, atau berat badan turun."
        )

    if "diare" in symptoms or "muntah" in symptoms or "mual" in symptoms:
        return make_result(
            "ringan-sedang",
            "gastroenteritis, gangguan pencernaan, atau keracunan makanan ringan",
            "Mual, muntah, dan diare sering berkaitan dengan gangguan saluran cerna akibat makanan, virus, atau bakteri.",
            "Minum cairan cukup, makan makanan ringan, dan hindari pedas/berminyak. Segera periksa bila BAB berdarah, muntah terus, tanda dehidrasi, demam tinggi, atau nyeri perut hebat."
        )

    if "nyeri perut" in symptoms:
        return make_result(
            "sedang",
            "nyeri perut non-spesifik, gangguan lambung, infeksi saluran cerna, atau masalah organ perut lain",
            "Nyeri perut perlu dilihat lokasi, intensitas, durasi, dan gejala penyerta seperti muntah, diare, demam, atau BAB berdarah.",
            "Periksa segera bila nyeri hebat, perut keras, muntah terus, demam tinggi, BAB berdarah, atau nyeri berpindah ke kanan bawah."
        )

    return None


def analyze_skin(symptoms, duration_days):
    if "luka bernanah" in symptoms:
        return make_result(
            "sedang-tinggi",
            "infeksi kulit atau luka terinfeksi",
            "Luka bernanah menandakan kemungkinan infeksi bakteri pada kulit atau jaringan sekitar.",
            "Jaga luka tetap bersih dan segera periksa ke fasilitas kesehatan, terutama bila makin merah, bengkak, nyeri, demam, atau nanah bertambah."
        )

    if "bentol" in symptoms or "gatal" in symptoms:
        return make_result(
            "ringan-sedang",
            "alergi kulit, biduran/urtikaria, iritasi, atau gigitan serangga",
            "Gatal dan bentol sering terkait reaksi alergi, iritasi, atau gigitan serangga.",
            "Hindari pemicu, jangan digaruk berlebihan. Segera periksa bila bengkak pada bibir/wajah, sesak napas, atau ruam menyebar cepat."
        )

    if "ruam" in symptoms:
        return make_result(
            "sedang",
            "ruam akibat alergi, infeksi virus, iritasi kulit, atau penyakit infeksi tertentu",
            "Ruam perlu dinilai dari bentuk, lokasi, gatal/tidak, disertai demam atau tidak.",
            "Periksa bila ruam disertai demam tinggi, nyeri, lepuh, perdarahan, atau menyebar cepat."
        )

    return None


def analyze_urinary(symptoms, duration_days):
    if "nyeri kencing" in symptoms or "sering kencing" in symptoms:
        return make_result(
            "sedang",
            "infeksi saluran kemih/ISK atau iritasi saluran kemih",
            "Nyeri saat kencing dan sering kencing sering mengarah ke infeksi saluran kemih, terutama bila disertai anyang-anyangan atau urine keruh.",
            "Minum cukup air dan periksa ke dokter untuk evaluasi urine, terutama bila demam, nyeri pinggang, urine berdarah, hamil, atau gejala berulang."
        )

    if "urine darah" in symptoms:
        return make_result(
            "tinggi",
            "urine berdarah yang perlu pemeriksaan langsung",
            "Urine berdarah bisa terkait infeksi, batu saluran kemih, atau penyebab lain yang perlu evaluasi.",
            "Sebaiknya segera periksa ke fasilitas kesehatan."
        )

    return None


def analyze_eye(symptoms, duration_days):
    if "penglihatan buram" in symptoms or "mata nyeri" in symptoms:
        return make_result(
            "sedang-tinggi",
            "gangguan mata yang perlu pemeriksaan, seperti infeksi mata berat, iritasi kornea, atau masalah tekanan mata",
            "Mata nyeri atau penglihatan buram perlu diperhatikan karena bisa menandakan masalah yang lebih serius.",
            "Segera periksa ke dokter mata bila nyeri berat, penglihatan menurun, mata sangat merah, keluar kotoran banyak, atau setelah trauma."
        )

    if "mata merah" in symptoms:
        return make_result(
            "ringan-sedang",
            "konjungtivitis/mata merah, iritasi, atau alergi",
            "Mata merah bisa disebabkan infeksi ringan, alergi, iritasi, atau mata kering.",
            "Jaga kebersihan tangan, hindari mengucek mata, jangan berbagi handuk. Periksa bila nyeri, buram, sangat silau, atau tidak membaik."
        )

    return None


def analyze_ent_dental(symptoms, duration_days):
    if "sakit gigi" in symptoms or "gusi bengkak" in symptoms:
        return make_result(
            "sedang",
            "gigi berlubang, radang gusi, atau abses gigi",
            "Sakit gigi dan gusi bengkak sering berkaitan dengan infeksi atau peradangan pada gigi/gusi.",
            "Sebaiknya periksa ke dokter gigi. Segera periksa bila bengkak wajah, demam, sulit membuka mulut, atau sulit menelan."
        )

    if "nyeri telinga" in symptoms or "keluar cairan telinga" in symptoms:
        return make_result(
            "sedang",
            "infeksi telinga, iritasi telinga, atau gangguan saluran telinga",
            "Nyeri telinga atau keluar cairan dapat terjadi karena infeksi telinga luar/tengah atau iritasi.",
            "Jangan memasukkan benda ke telinga. Periksa bila nyeri berat, demam, pendengaran menurun, atau keluar cairan/nanah."
        )

    return None


def analyze_neuro_muscle(symptoms, duration_days):
    if "lemah separuh badan" in symptoms:
        return make_result(
            "darurat",
            "gejala yang mengarah ke stroke atau gangguan saraf serius",
            "Lemah separuh badan, wajah mencong, atau bicara pelo merupakan tanda bahaya.",
            "Segera ke IGD. Jangan menunggu gejala hilang sendiri."
        )

    if "sakit kepala hebat" in symptoms:
        return make_result(
            "tinggi",
            "sakit kepala berat yang perlu evaluasi",
            "Sakit kepala hebat mendadak atau berbeda dari biasanya bisa menjadi tanda kondisi serius.",
            "Segera periksa bila sangat berat, disertai kaku leher, muntah hebat, gangguan penglihatan, lemah anggota tubuh, atau penurunan kesadaran."
        )

    if "nyeri sendi" in symptoms or "bengkak sendi" in symptoms:
        return make_result(
            "ringan-sedang",
            "radang sendi, cedera ringan, asam urat, atau infeksi tertentu bila disertai demam",
            "Nyeri sendi bisa disebabkan banyak hal, dari cedera, peradangan, sampai infeksi.",
            "Istirahatkan sendi, hindari aktivitas berat. Periksa bila bengkak hebat, merah, panas, demam, atau sulit digerakkan."
        )

    if "nyeri punggung" in symptoms:
        return make_result(
            "ringan-sedang",
            "nyeri otot punggung, postur/aktivitas berat, atau gangguan saraf pinggang",
            "Nyeri punggung sering terkait otot tegang, postur, atau aktivitas berat.",
            "Istirahat relatif, kompres hangat, dan perbaiki postur. Periksa bila nyeri menjalar ke kaki, kebas, lemah, gangguan BAB/BAK, atau setelah trauma."
        )

    return None


def analyze_reproductive(symptoms, duration_days):
    if "nyeri haid" in symptoms:
        return make_result(
            "ringan-sedang",
            "nyeri haid/dismenore",
            "Nyeri haid sering terjadi karena kontraksi rahim saat menstruasi. Namun nyeri sangat berat bisa berkaitan dengan kondisi lain.",
            "Kompres hangat dan istirahat. Periksa bila nyeri sangat berat, haid sangat banyak, pingsan, atau mengganggu aktivitas berat."
        )

    if "haid tidak teratur" in symptoms or "keputihan" in symptoms:
        return make_result(
            "sedang",
            "gangguan hormonal, infeksi, atau kondisi reproduksi lain",
            "Keluhan haid tidak teratur atau keputihan perlu dinilai dari durasi, bau, warna, gatal, nyeri, dan kemungkinan kehamilan.",
            "Sebaiknya konsultasi ke dokter/bidan, terutama bila keputihan berbau, gatal berat, nyeri perut bawah, perdarahan banyak, atau telat haid lama."
        )

    return None


def medical_reply(message, history):
    text = merge_user_text(history, message)
    symptoms = detect_symptoms(text)
    age = detect_age(text)
    duration_days = detect_duration_days(text)
    temperature = detect_temperature(text)

    emergency_reasons = emergency_check(text, symptoms, temperature)
    if emergency_reasons:
        return (
            "Tanda bahaya terdeteksi.\n\n"
            f"Alasan: {', '.join(emergency_reasons)}.\n\n"
            "Sebaiknya segera ke IGD atau hubungi tenaga medis terdekat. "
            "Chatbot ini hanya membantu skrining awal dan bukan pengganti diagnosis dokter."
        )

    if not symptoms:
        return (
            "Boleh jelaskan keluhan utama Anda? Contohnya batuk, demam, pilek, "
            "sakit tenggorokan, mual, muntah, diare, nyeri perut, ruam, gatal, "
            "nyeri kencing, sakit gigi, mata merah, telinga sakit, sesak, atau nyeri dada."
        )

    missing = ask_missing_info(symptoms, age, duration_days, temperature, text)
    if missing:
        return (
            f"Saya menangkap gejala: {', '.join(symptoms)}.\n\n"
            f"Boleh lengkapi dulu: {', '.join(missing)}?"
        )

    result = None

    if any(symptom in symptoms for symptom in [
        "batuk",
        "pilek",
        "sakit tenggorokan",
        "sesak napas",
        "nyeri dada",
        "dahak",
        "dahak darah",
        "hidung tersumbat",
    ]):
        result = analyze_respiratory(symptoms, duration_days, temperature)

    elif "demam" in symptoms:
        result = analyze_fever(symptoms, duration_days, temperature)

    elif any(symptom in symptoms for symptom in [
        "mual",
        "muntah",
        "diare",
        "nyeri perut",
        "perut kembung",
        "nyeri ulu hati",
    ]):
        result = analyze_digestive(symptoms, duration_days)

    elif any(symptom in symptoms for symptom in [
        "ruam",
        "gatal",
        "bentol",
        "luka bernanah",
    ]):
        result = analyze_skin(symptoms, duration_days)

    elif any(symptom in symptoms for symptom in [
        "nyeri kencing",
        "sering kencing",
        "urine darah",
    ]):
        result = analyze_urinary(symptoms, duration_days)

    elif any(symptom in symptoms for symptom in [
        "mata merah",
        "mata nyeri",
        "penglihatan buram",
    ]):
        result = analyze_eye(symptoms, duration_days)

    elif any(symptom in symptoms for symptom in [
        "sakit gigi",
        "gusi bengkak",
        "nyeri telinga",
        "keluar cairan telinga",
    ]):
        result = analyze_ent_dental(symptoms, duration_days)

    elif any(symptom in symptoms for symptom in [
        "lemah separuh badan",
        "sakit kepala hebat",
        "nyeri sendi",
        "bengkak sendi",
        "nyeri punggung",
    ]):
        result = analyze_neuro_muscle(symptoms, duration_days)

    elif any(symptom in symptoms for symptom in [
        "nyeri haid",
        "haid tidak teratur",
        "keputihan",
    ]):
        result = analyze_reproductive(symptoms, duration_days)

    if not result:
        result = make_result(
            "belum spesifik",
            "keluhan umum yang perlu dipantau",
            "Gejala yang disebutkan belum cukup spesifik untuk mengarah ke satu kemungkinan penyakit tertentu.",
            "Pantau gejala dan konsultasikan ke dokter bila memburuk atau tidak membaik."
        )

    return (
        "Hasil analisis awal R Hospital:\n\n"
        f"Tingkat perhatian: {result['level']}.\n\n"
        f"Kemungkinan:\n{result['kemungkinan']}.\n\n"
        f"Penjelasan:\n{result['penjelasan']}\n\n"
        f"Saran awal:\n{result['saran']}\n\n"
        "Catatan: ini bukan diagnosis pasti. Diagnosis tetap perlu pemeriksaan langsung oleh tenaga medis."
    )


@app.post("/chat")
def chat(request: dict):
    user_message = request.get("message", "")
    history = request.get("history", [])

    reply = medical_reply(user_message, history)

    return {"reply": reply}