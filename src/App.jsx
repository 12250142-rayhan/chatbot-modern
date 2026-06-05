import { useEffect, useRef, useState } from "react";

const API_URL = "https://r-hospital-api-v3.vercel.app";

const quickPrompts = [
  "Saya demam 1 hari umur 19 tahun",
  "Saya batuk sudah 2 hari umur 19 tahun",
  "Saya sakit perut dan mual 1 hari",
  "Saya sesak napas dan nyeri dada",
];

export default function ModernChatbot() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const [messages, setMessages] = useState([
    {
      role: "bot",
      text:
        "Halo! Selamat datang di R Hospital 👋\n\nSaya bisa membantu skrining awal berdasarkan gejala. Ceritakan keluhan Anda, umur, dan sudah berapa lama gejalanya.",
    },
  ]);

  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

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
      const response = await fetch(`${API_URL}/chat`, {
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
          text: data.reply || "Maaf, saya belum bisa menjawab.",
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
        text:
          "Halo! Selamat datang di R Hospital 👋\n\nSaya bisa membantu skrining awal berdasarkan gejala. Ceritakan keluhan Anda, umur, dan sudah berapa lama gejalanya.",
      },
    ]);
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_#064e3b,_transparent_35%),linear-gradient(135deg,_#020617,_#0f172a,_#111827)] text-white flex items-center justify-center p-4 md:p-8">
      <div className="w-full max-w-6xl h-[90vh] grid grid-cols-1 md:grid-cols-[320px_1fr] gap-4">
        <aside className="hidden md:flex flex-col justify-between rounded-3xl border border-white/10 bg-white/10 backdrop-blur-xl p-6 shadow-2xl">
          <div>
            <div className="flex items-center gap-3 mb-8">
              <div className="h-12 w-12 rounded-2xl bg-emerald-400 text-slate-950 flex items-center justify-center font-black text-xl">
                R
              </div>
              <div>
                <h1 className="text-2xl font-bold">R Hospital</h1>
                <p className="text-sm text-slate-300">Medical Assistant</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="rounded-2xl bg-emerald-400/10 border border-emerald-400/20 p-4">
                <div className="flex items-center gap-2 text-emerald-300 font-semibold">
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  Backend Online
                </div>
                <p className="text-sm text-slate-300 mt-2">
                  Sistem siap menerima keluhan pasien.
                </p>
              </div>

              <div className="rounded-2xl bg-white/5 border border-white/10 p-4">
                <h2 className="font-semibold mb-2">Cara pakai</h2>
                <p className="text-sm text-slate-300 leading-relaxed">
                  Tulis keluhan, umur, durasi gejala, dan gejala tambahan.
                  Contoh: “Saya batuk 2 hari umur 19 tahun”.
                </p>
              </div>

              <div className="rounded-2xl bg-amber-400/10 border border-amber-400/20 p-4">
                <h2 className="font-semibold text-amber-200 mb-2">
                  Disclaimer
                </h2>
                <p className="text-sm text-slate-300 leading-relaxed">
                  Ini hanya skrining awal, bukan diagnosis pasti. Jika ada tanda tanda
                  darurat, segera ke IGD.
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
          <header className="px-5 md:px-7 py-5 border-b border-white/10 bg-white/5 flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3">
                <div className="md:hidden h-10 w-10 rounded-2xl bg-emerald-400 text-slate-950 flex items-center justify-center font-black">
                  R
                </div>
                <div>
                  <h1 className="text-xl md:text-2xl font-bold">
                    NM Hospital Chat
                  </h1>
                  <p className="text-xs md:text-sm text-slate-300">
                    Skrining awal keluhan pasien
                  </p>
                </div>
              </div>
            </div>

            <div className="hidden sm:flex items-center gap-2 rounded-full bg-emerald-400/10 border border-emerald-400/20 px-4 py-2 text-sm text-emerald-300">
              <span className="h-2 w-2 rounded-full bg-emerald-400"></span>
              Online
            </div>
          </header>

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
                  <div
                    className={`h-9 w-9 shrink-0 rounded-2xl flex items-center justify-center text-sm font-bold ${
                      msg.role === "user"
                        ? "bg-emerald-400 text-slate-950"
                        : "bg-white/10 text-white border border-white/10"
                    }`}
                  >
                    {msg.role === "user" ? "U" : "R"}
                  </div>

                  <div>
                    <div
                      className={`px-5 py-4 rounded-3xl leading-relaxed whitespace-pre-line shadow-lg ${
                        msg.role === "user"
                          ? "bg-emerald-400 text-slate-950 rounded-tr-md"
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
                      {msg.role === "user" ? "Pasien" : "R Hospital Assistant"}
                    </p>
                  </div>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="flex gap-3 max-w-[78%]">
                  <div className="h-9 w-9 rounded-2xl bg-white/10 border border-white/10 flex items-center justify-center text-sm font-bold">
                    R
                  </div>
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
            <div className="flex gap-2 overflow-x-auto pb-2">
              {quickPrompts.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => sendMessage(prompt)}
                  disabled={loading}
                  className="shrink-0 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 px-4 py-2 text-xs text-slate-200 transition disabled:opacity-50"
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
                placeholder="Contoh: saya batuk sudah 2 hari umur 19 tahun..."
                className="flex-1 bg-slate-950/40 border border-white/10 text-white placeholder:text-slate-500 rounded-2xl px-5 py-4 outline-none focus:border-emerald-400/60 focus:ring-2 focus:ring-emerald-400/20 transition"
              />

              <button
                onClick={() => sendMessage()}
                disabled={loading || !input.trim()}
                className="bg-emerald-400 hover:bg-emerald-300 transition px-5 md:px-7 rounded-2xl text-slate-950 font-bold disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-emerald-500/10"
              >
                Kirim
              </button>
            </div>

            <p className="text-[11px] text-slate-400 mt-3 text-center">
              R Hospital Assistant hanya membantu skrining awal. Untuk kondisi
              darurat, segera hubungi IGD atau fasilitas kesehatan terdekat.
            </p>
          </footer>
        </main>
      </div>
    </div>
  );
}