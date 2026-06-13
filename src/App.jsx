import { useEffect, useRef, useState } from "react";

const API_URL = "https://r-hospital-api-v3.vercel.app";

const screeningPrompts = [
  "Saya demam 1 hari umur 19 tahun",
  "Saya batuk sudah 2 hari umur 19 tahun",
  "Saya sakit perut dan mual 1 hari",
  "Saya sesak napas dan nyeri dada",
];

const susanPrompts = [
  "Makanan apa yang bagus untuk menjaga imun?",
  "Bagaimana cara menjaga pola tidur?",
  "Apa tips hidup sehat untuk pekerja kantoran?",
  "Olahraga ringan apa yang bisa dilakukan di rumah?",
];

function HospitalLogo({ small = false }) {
  const size = small ? "w-10 h-10" : "w-14 h-14";

  return (
    <div
      className={`${size} rounded-2xl bg-emerald-500 flex items-center justify-center shadow-lg`}
    >
      <svg
        viewBox="0 0 64 64"
        className={small ? "w-6 h-6" : "w-8 h-8"}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect x="14" y="10" width="36" height="44" rx="4" fill="white" />
        <rect x="28" y="18" width="8" height="20" rx="1" fill="#10b981" />
        <rect x="22" y="24" width="20" height="8" rx="1" fill="#10b981" />
        <rect x="20" y="42" width="8" height="12" rx="1" fill="#cbd5e1" />
        <rect x="36" y="42" width="8" height="12" rx="1" fill="#cbd5e1" />
      </svg>
    </div>
  );
}

function SusanAvatar({ small = false }) {
  const size = small ? "w-10 h-10" : "w-14 h-14";
  const textSize = small ? "text-lg" : "text-2xl";

  return (
    <div
      className={`${size} rounded-2xl bg-gradient-to-br from-emerald-300 via-cyan-300 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20 border border-white/30`}
    >
      <div className="w-[72%] h-[72%] rounded-xl bg-slate-950/80 flex items-center justify-center">
        <span className={`${textSize} font-black text-emerald-300`}>S</span>
      </div>
    </div>
  );
}

export default function ModernChatbot() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState("screening");
  const cleanBotText = (text = "") => {
  return text
    .replace(/\*\*/g, "")
    .replace(/\*/g, "")
    .trim();
};

  const getWelcomeMessage = (selectedMode = mode) => {
    if (selectedMode === "susan") {
      return "Halo! Saya Susan, asisten kesehatan AI R Hospital.\n\nSilakan tanyakan seputar kesehatan umum, pola makan, gaya hidup sehat, gejala ringan, atau perawatan awal yang aman.";
    }

    return "Halo! Selamat datang di R Hospital 👋\n\nSaya bisa membantu skrining awal berdasarkan gejala. Ceritakan keluhan Anda, umur, dan sudah berapa lama gejalanya.";
  };

  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: getWelcomeMessage("screening"),
    },
  ]);

  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  const changeMode = (selectedMode) => {
    setMode(selectedMode);
    setInput("");
    setMessages([
      {
        role: "bot",
        text: getWelcomeMessage(selectedMode),
      },
    ]);
  };

  const sendMessage = async (customInput) => {
    const finalInput = customInput || input;

    if (!finalInput.trim() || loading) return;

    const userInput = finalInput.trim();

    const updatedMessages = [
      ...messages,
      {
        role: "user",
        text: userInput,
      },
    ];

    setMessages(updatedMessages);
    setInput("");
    setLoading(true);

    try {
      const endpoint = mode === "susan" ? "/ask-doctor" : "/chat";

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: userInput,
          history: updatedMessages,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: cleanBotText(data.reply || "Maaf, saya belum bisa menjawab."),
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text:
            "Server error. Backend belum bisa diakses atau CORS belum benar.\n\nDetail: " +
            error.message,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        role: "bot",
        text: getWelcomeMessage(mode),
      },
    ]);
  };

  const activePrompts = mode === "susan" ? susanPrompts : screeningPrompts;
  const isSusan = mode === "susan";

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_#064e3b,_transparent_35%),linear-gradient(135deg,_#020617,_#0f172a,_#111827)] text-white flex items-center justify-center p-4 md:p-8">
      <div className="w-full max-w-6xl h-[90vh] grid grid-cols-1 md:grid-cols-[320px_1fr] gap-4">
        <aside className="hidden md:flex flex-col justify-between rounded-3xl border border-white/10 bg-white/10 backdrop-blur-xl p-6 shadow-2xl">
          <div>
            <div className="flex items-center gap-3 mb-8">
              <HospitalLogo />
              <div>
                <h1 className="text-2xl font-bold">R Hospital</h1>
                <p className="text-sm text-slate-300">Medical Assistant</p>
              </div>
            </div>

            <div className="space-y-4">
              <button
                onClick={() => changeMode("susan")}
                className={`w-full text-left rounded-3xl border p-5 transition group ${
                  isSusan
                    ? "bg-gradient-to-br from-emerald-400 via-teal-300 to-cyan-300 text-slate-950 border-emerald-200 shadow-lg shadow-emerald-500/20"
                    : "bg-white/5 border-white/10 hover:bg-white/10"
                }`}
              >
                <div className="flex items-center gap-3">
                  <SusanAvatar small />
                  <div>
                    <h2
                      className={`font-bold ${
                        isSusan ? "text-slate-950" : "text-white"
                      }`}
                    >
                      Tanya Susan
                    </h2>
                    <p
                      className={`text-sm mt-1 ${
                        isSusan ? "text-slate-800" : "text-slate-300"
                      }`}
                    >
                      Chat AI kesehatan yang lebih fleksibel.
                    </p>
                  </div>
                </div>
              </button>

              <button
                onClick={() => changeMode("screening")}
                className={`w-full text-left rounded-3xl border p-5 transition ${
                  !isSusan
                    ? "bg-emerald-400 text-slate-950 border-emerald-300 shadow-lg shadow-emerald-500/20"
                    : "bg-white/5 border-white/10 hover:bg-white/10"
                }`}
              >
                <div className="flex items-center gap-3">
                  <HospitalLogo small />
                  <div>
                    <h2 className="font-bold">Skrining Gejala</h2>
                    <p
                      className={`text-sm mt-1 ${
                        !isSusan ? "text-slate-800" : "text-slate-300"
                      }`}
                    >
                      Analisis awal berdasarkan keluhan pasien.
                    </p>
                  </div>
                </div>
              </button>

              <div
                className={`rounded-3xl border p-5 ${
                  isSusan
                    ? "bg-fuchsia-400/10 border-fuchsia-300/20"
                    : "bg-amber-400/10 border-amber-400/20"
                }`}
              >
                <h2
                  className={`font-semibold mb-2 ${
                    isSusan ? "text-fuchsia-200" : "text-amber-200"
                  }`}
                >
                  {isSusan ? "Mode Susan" : "Disclaimer"}
                </h2>
                <p className="text-sm text-slate-300 leading-relaxed">
                  {isSusan
                    ? "Cocok untuk tanya jawab kesehatan umum, pola makan, kebiasaan sehat, dan edukasi ringan."
                    : "Ini hanya skrining awal, bukan diagnosis pasti. Diagnosis tetap perlu pemeriksaan langsung oleh tenaga medis."}
                </p>
              </div>
            </div>
          </div>

          <button
            onClick={clearChat}
            className="w-full rounded-2xl border border-white/10 bg-white/5 hover:bg-white/10 transition px-4 py-3 text-sm font-semibold"
          >
            Reset Chat
          </button>
        </aside>

        <main className="rounded-3xl border border-white/10 bg-white/10 backdrop-blur-xl shadow-2xl flex flex-col overflow-hidden">
          <header
            className={`px-5 md:px-7 py-5 border-b border-white/10 flex items-center justify-between ${
              isSusan
                ? "bg-gradient-to-r from-fuchsia-500/10 via-emerald-400/10 to-cyan-400/10"
                : "bg-white/5"
            }`}
          >
            <div>
              <div className="flex items-center gap-3">
                <div className="md:hidden">
                  {isSusan ? <SusanAvatar small /> : <HospitalLogo small />}
                </div>

                <div>
                  <h1 className="text-xl md:text-2xl font-bold">
                    {isSusan ? "Tanya Susan" : "R Hospital Chat"}
                  </h1>
                  <p className="text-xs md:text-sm text-slate-300">
                    {isSusan
                      ? "Asisten kesehatan AI R Hospital"
                      : "Skrining awal keluhan pasien"}
                  </p>
                </div>
              </div>
            </div>

            <div className="hidden sm:flex items-center gap-2 rounded-full bg-emerald-400/10 border border-emerald-400/20 px-4 py-2 text-sm text-emerald-300">
              <span className="h-2 w-2 rounded-full bg-emerald-400"></span>
              Online
            </div>
          </header>

          {isSusan && (
            <div className="px-5 md:px-7 py-4 border-b border-white/10 bg-slate-950/20">
              <div className="rounded-3xl bg-gradient-to-r from-fuchsia-400/10 via-emerald-400/10 to-cyan-400/10 border border-white/10 p-4 flex items-center gap-4">
                <SusanAvatar small />
                <div>
                  <h2 className="font-bold">Halo, saya Susan</h2>
                  <p className="text-sm text-slate-300 mt-1">
                    Tanyakan seputar pola makan, gaya hidup sehat, keluhan
                    ringan, atau edukasi kesehatan umum.
                  </p>
                </div>
              </div>
            </div>
          )}

          <section className="flex-1 overflow-y-auto p-5 md:p-7 space-y-5">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`flex gap-3 max-w-[90%] md:max-w-[78%] ${
                    msg.role === "user" ? "flex-row-reverse" : "flex-row"
                  }`}
                >
                  {msg.role === "user" ? (
                    <div className="h-9 w-9 shrink-0 rounded-2xl bg-emerald-400 text-slate-950 flex items-center justify-center text-sm font-bold">
                      U
                    </div>
                  ) : isSusan ? (
                    <SusanAvatar small />
                  ) : (
                    <HospitalLogo small />
                  )}

                  <div>
                    <div
                      className={`px-5 py-4 rounded-3xl leading-relaxed whitespace-pre-line shadow-lg ${
                        msg.role === "user"
                          ? "bg-emerald-400 text-slate-950 rounded-tr-md"
                          : isSusan
                          ? "bg-gradient-to-br from-white/15 to-fuchsia-400/10 text-white border border-fuchsia-300/20 rounded-tl-md"
                          : "bg-white/10 text-white border border-white/10 rounded-tl-md"
                      }`}
                    >
                      {msg.text}
                    </div>
                    <p
                      className={`text-[11px] mt-1 text-slate-400 ${
                        msg.role === "user" ? "text-right" : "text-left"
                      }`}
                    >
                      {msg.role === "user"
                        ? "Pasien"
                        : isSusan
                        ? "Susan"
                        : "R Hospital Assistant"}
                    </p>
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="flex gap-3 max-w-[78%]">
                  {isSusan ? <SusanAvatar small /> : <HospitalLogo small />}
                  <div className="bg-white/10 text-white px-5 py-4 rounded-3xl rounded-tl-md border border-white/10">
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-slate-300 animate-bounce"></span>
                      <span className="h-2 w-2 rounded-full bg-slate-300 animate-bounce [animation-delay:120ms]"></span>
                      <span className="h-2 w-2 rounded-full bg-slate-300 animate-bounce [animation-delay:240ms]"></span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div ref={bottomRef}></div>
          </section>

          <div className="px-5 md:px-7 pb-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {activePrompts.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => sendMessage(prompt)}
                  disabled={loading}
                  className={`rounded-2xl border px-4 py-3 text-left text-xs md:text-sm transition disabled:opacity-50 ${
                    isSusan
                      ? "bg-fuchsia-400/10 hover:bg-fuchsia-400/20 border-fuchsia-300/20 text-fuchsia-50"
                      : "bg-white/5 hover:bg-white/10 border-white/10 text-slate-200"
                  }`}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>

          <footer className="p-4 md:p-5 border-t border-white/10 bg-white/5">
            <div className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  isSusan
                    ? "Tulis pertanyaan untuk Susan..."
                    : "Contoh: saya batuk sudah 2 hari umur 19 tahun..."
                }
                className={`flex-1 bg-slate-950/40 border text-white placeholder:text-slate-500 rounded-2xl px-5 py-4 outline-none focus:ring-2 transition ${
                  isSusan
                    ? "border-fuchsia-300/30 focus:border-fuchsia-300/70 focus:ring-fuchsia-300/20"
                    : "border-white/10 focus:border-emerald-400/60 focus:ring-emerald-400/20"
                }`}
              />

              <button
                onClick={() => sendMessage()}
                disabled={loading || !input.trim()}
                className={`transition px-5 md:px-7 rounded-2xl font-bold disabled:opacity-50 disabled:cursor-not-allowed shadow-lg ${
                  isSusan
                    ? "bg-gradient-to-r from-fuchsia-300 to-emerald-300 hover:opacity-90 text-slate-950 shadow-fuchsia-500/10"
                    : "bg-emerald-400 hover:bg-emerald-300 text-slate-950 shadow-emerald-500/10"
                }`}
              >
                Kirim
              </button>
            </div>

            <p className="text-[11px] text-slate-400 mt-3 text-center">
              {isSusan
                ? "Susan adalah asisten kesehatan AI untuk edukasi umum, bukan pengganti pemeriksaan dokter."
                : "R Hospital Assistant hanya membantu skrining awal. Diagnosis tetap perlu pemeriksaan langsung oleh tenaga medis."}
            </p>
          </footer>
        </main>
      </div>
    </div>
  );
}