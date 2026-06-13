import os
import requests
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from screening_engine import screening_reply

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        httplocalhost5173,
        http127.0.0.15173,
        httpschatbot-modern-eight.vercel.app,
        httpschatbot-modern.vercel.app,
    ],
    allow_origin_regex=rhttps..vercel.app,
    allow_credentials=True,
    allow_methods=[],
    allow_headers=[],
)

GEMINI_API_KEY = os.getenv(GEMINI_API_KEY, )
GEMINI_MODEL = os.getenv(GEMINI_MODEL, gemini-2.5-flash)

GROQ_API_KEY = os.getenv(GROQ_API_KEY, )
GROQ_MODEL = os.getenv(GROQ_MODEL, llama-3.1-8b-instant)

USE_GEMINI = os.getenv(USE_GEMINI, false).lower() == true

DOCTOR_SCHEDULE = {
    0 {
        00-08 {name Dr. Rayhan, phone +6398878802928},
        08-16 {name Dr. Hapid Mizan, phone +6344878029529},
        16-00 {name Dr. Rini Hermi, phone +6342548029777},
    },
    1 {
        00-08 {name Dr. Hapid Mizan, phone +6344878029529},
        08-16 {name Dr. Rini Hermi, phone +6342548029777},
        16-00 {name Dr. Adif Rizal, phone +6342548092021},
    },
    2 {
        00-08 {name Dr. Rini Hermi, phone +6342548029777},
        08-16 {name Dr. Adif Rizal, phone +6342548092021},
        16-00 {name Dr. Rayhan, phone +6398878802928},
    },
    3 {
        00-08 {name Dr. Adif Rizal, phone +6342548092021},
        08-16 {name Dr. Rayhan, phone +6398878802928},
        16-00 {name Dr. Hapid Mizan, phone +6344878029529},
    },
    4 {
        00-08 {name Dr. Rayhan, phone +6398878802928},
        08-16 {name Dr. Rini Hermi, phone +6342548029777},
        16-00 {name Dr. Adif Rizal, phone +6342548092021},
    },
    5 {
        00-08 {name Dr. Hapid Mizan, phone +6344878029529},
        08-16 {name Dr. Adif Rizal, phone +6342548092021},
        16-00 {name Dr. Rayhan, phone +6398878802928},
    },
    6 {
        00-08 {name Dr. Rini Hermi, phone +6342548029777},
        08-16 {name Dr. Rayhan, phone +6398878802928},
        16-00 {name Dr. Hapid Mizan, phone +6344878029529},
    },
}


def get_on_duty_doctor()
    now = datetime.now(timezone(timedelta(hours=7)))
    weekday = now.weekday()
    hour = now.hour

    if 0 = hour  8
        shift = 00-08
        display_shift = 0000 - 0800 WIB (1200 AM - 800 AM)
    elif 8 = hour  16
        shift = 08-16
        display_shift = 0800 - 1600 WIB (800 AM - 400 PM)
    else
        shift = 16-00
        display_shift = 1600 - 0000 WIB (400 PM - 1200 AM)

    doctor = DOCTOR_SCHEDULE[weekday][shift]

    return {
        name doctor[name],
        phone doctor[phone],
        shift display_shift,
    }


@app.get()
def home()
    return {
        message R Hospital Backend is running
    }


@app.get(test)
def test()
    return {
        status ok
    }


@app.get(version)
def version()
    return {
        app R Hospital Backend,
        version dataset-engine-groq-susan-v1,
        screening_engine dataset_rule_based_scoring,
        ai_provider groq-primary-gemini-optional,
        use_gemini USE_GEMINI,
        gemini_model GEMINI_MODEL,
        groq_model GROQ_MODEL,
        duration_fix True,
    }


@app.post(chat)
def chat(request dict)
    user_message = request.get(message, )
    history = request.get(history, [])

    reply = screening_reply(
        user_message,
        history,
        on_duty_doctor=get_on_duty_doctor()
    )

    return {
        reply reply
    }


@app.post(ask-doctor)
def ask_doctor(request dict)
    user_message = request.get(message, )
    history = request.get(history, [])

    if not user_message.strip()
        return {
            reply Silakan tuliskan pertanyaan kesehatan yang ingin Anda tanyakan kepada Susan.
        }

    system_prompt = (
        Kamu adalah Susan, seorang asisten kesehatan AI perempuan untuk R Hospital yang memiliki empati kepada manusia. 
        Jawab dalam bahasa Indonesia yang ramah, jelas, singkat, dan mudah dipahami. 
        Tugasmu menjawab pertanyaan kesehatan umum, edukasi gejala, menjaga pola makan dan tips hidup sehat, 
        perawatan awal yang aman, penjelasan obat umum, dan kapan pasien perlu periksa. 
        Jangan memberikan diagnosis pasti. 
        Jangan membuat resep obat keras atau antibiotik. 
        Jawab maksimal 5 poin singkat. 
        Untuk kondisi keracunan, jangan menyarankan obat resep. Sarankan bilas mulut, minum air sedikit-sedikit bila sadar, 
        jangan paksa muntah, dan segera ke IGD bila tertelan bahan kimia, sesak, muntah terus, nyeri hebat, atau penurunan kesadaran.
    )

    gemini_error = Gemini dilewati

    if USE_GEMINI and GEMINI_API_KEY
        gemini_contents = [
            {
                role user,
                parts [{text system_prompt}],
            }
        ]

        for msg in history[-6]
            role = msg.get(role)
            text = msg.get(text, )

            if not text
                continue

            if text.strip() == user_message.strip()
                continue

            gemini_role = user if role == user else model
            gemini_contents.append(
                {
                    role gemini_role,
                    parts [{text text}],
                }
            )

        gemini_contents.append(
            {
                role user,
                parts [{text user_message}],
            }
        )

        try
            gemini_response = requests.post(
                fhttpsgenerativelanguage.googleapis.comv1betamodels{GEMINI_MODEL}generateContent,
                headers={
                    x-goog-api-key GEMINI_API_KEY,
                    Content-Type applicationjson,
                },
                json={
                    contents gemini_contents,
                    generationConfig {
                        temperature 0.3,
                        maxOutputTokens 500,
                    },
                },
                timeout=10,
            )

            if gemini_response.status_code == 200
                data = gemini_response.json()
                reply = data[candidates][0][content][parts][0][text]
                return {
                    reply reply
                }

            gemini_error = fGemini error {gemini_response.status_code} {gemini_response.text[200]}

        except Exception as error
            gemini_error = fGemini exception {str(error)}

    if GROQ_API_KEY
        try
            groq_messages = [
                {
                    role system,
                    content system_prompt,
                }
            ]

            for msg in history[-6]
                role = msg.get(role)
                text = msg.get(text, )

                if not text
                    continue

                if text.strip() == user_message.strip()
                    continue

                if role == user
                    groq_messages.append({role user, content text})
                elif role == bot
                    groq_messages.append({role assistant, content text})

            groq_messages.append(
                {
                    role user,
                    content user_message,
                }
            )

            groq_response = requests.post(
                httpsapi.groq.comopenaiv1chatcompletions,
                headers={
                    Authorization fBearer {GROQ_API_KEY},
                    Content-Type applicationjson,
                },
                json={
                    model GROQ_MODEL,
                    messages groq_messages,
                    temperature 0.3,
                    max_tokens 500,
                },
                timeout=20,
            )

            if groq_response.status_code != 200
                return {
                    reply (
                        Maaf, layanan Tanya Susan sedang tidak bisa diakses. 
                        fGemini {gemini_error}. 
                        fGroq error {groq_response.status_code} {groq_response.text[200]}
                    )
                }

            data = groq_response.json()
            reply = data[choices][0][message][content]

            return {
                reply reply
            }

        except Exception as error
            return {
                reply (
                    Maaf, layanan Tanya Susan sedang gangguan. 
                    fGemini {gemini_error}. 
                    fGroq exception {str(error)}
                )
            }

    return {
        reply (
            Maaf, layanan Tanya Susan sedang tidak bisa diakses. 
            fDetail {gemini_error}. Groq API key belum diset.
        )
    }