import { useEffect, useRef, useState } from "react";

export default function ModernChatbot() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: "Halo! Selamat datang di R Hospital 👋",
    },
  ]);

  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userInput = input;

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
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: userInput,
          history: updatedMessages,
        }),
      });

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
          text: "Server error: " + error.message,
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 flex items-center justify-center p-6">
      <div className="w-full max-w-4xl h-[85vh] bg-white/10 backdrop-blur-xl border border-white/10 rounded-3xl shadow-2xl flex flex-col overflow-hidden">
        <div className="px-6 py-4 border-b border-white/10 bg-white/5">
          <h1 className="text-white text-2xl font-bold">R Hospital</h1>
          <p className="text-slate-300 text-sm">Layanan chat Rumah sakit</p>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[75%] px-5 py-4 rounded-3xl ${
                  msg.role === "user"
                    ? "bg-emerald-400 text-black"
                    : "bg-white/10 text-white"
                }`}
              >
                {msg.text}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-white/10 text-white px-5 py-4 rounded-3xl">
                sedang mengetik...
              </div>
            </div>
          )}

          <div ref={bottomRef}></div>
        </div>

        <div className="p-5 border-t border-white/10 bg-white/5">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Tulis pesan..."
              className="flex-1 bg-white/10 border border-white/10 text-white placeholder:text-slate-400 rounded-2xl px-5 py-4 outline-none"
            />

            <button
              onClick={sendMessage}
              disabled={loading}
              className="bg-emerald-400 hover:bg-emerald-300 transition px-6 rounded-2xl text-black font-semibold disabled:opacity-50"
            >
              Kirim
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}