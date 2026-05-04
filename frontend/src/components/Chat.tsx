import { useState } from "react";
import { api } from "../lib/api";

interface Turn {
  role: "user" | "model";
  content: string;
}

export default function Chat() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [busy, setBusy] = useState(false);

  const send = async (e?: React.FormEvent) => {
    e?.preventDefault();
    const message = input.trim();
    if (!message || busy) return;
    setInput("");
    setTurns((t) => [...t, { role: "user", content: message }]);
    setBusy(true);
    try {
      const r = await api.ask(message, sessionId);
      setSessionId(r.data.session_id);
      setTurns((t) => [...t, { role: "model", content: r.data.answer }]);
    } catch (err) {
      setTurns((t) => [...t, { role: "model", content: "Sorry, I could not reach the agent." }]);
    } finally {
      setBusy(false);
    }
  };

  const examples = [
    "What sports does the Pacific Northwest excel at?",
    "Compare Hawaii and Vermont for Team USA representation.",
    "Which state has the strongest Paralympic adaptive-sports presence?",
  ];

  return (
    <div className="rounded-xl border border-ink-200 bg-white p-5 space-y-4">
      <div className="flex items-baseline justify-between">
        <h3 className="font-display font-semibold text-base">Ask anything about Team USA hubs</h3>
        <span className="text-xs text-ink-500">Powered by Gemini, grounded in aggregate data</span>
      </div>

      {turns.length === 0 ? (
        <div className="space-y-2">
          <p className="text-sm text-ink-500">Try one of these:</p>
          <div className="flex flex-wrap gap-2">
            {examples.map((ex) => (
              <button
                key={ex}
                onClick={() => setInput(ex)}
                className="text-xs px-3 py-1.5 rounded-full border border-ink-200 hover:bg-olympic-50 hover:border-olympic-500"
              >
                {ex}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {turns.map((t, i) => (
            <div key={i} className={t.role === "user" ? "text-right" : "text-left"}>
              <div
                className={`inline-block max-w-[85%] px-4 py-2 rounded-2xl text-sm leading-relaxed ${
                  t.role === "user"
                    ? "bg-olympic-500 text-white"
                    : "bg-ink-50 text-ink-900 border border-ink-200"
                }`}
              >
                {t.content}
              </div>
            </div>
          ))}
          {busy && <div className="text-sm text-ink-500 italic">Thinking...</div>}
        </div>
      )}

      <form onSubmit={send} className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about a region, sport, or hub..."
          disabled={busy}
          className="flex-1 px-4 py-2 rounded-lg border border-ink-200 focus:outline-none focus:ring-2 focus:ring-olympic-500"
        />
        <button
          type="submit"
          disabled={busy || !input.trim()}
          className="px-4 py-2 rounded-lg bg-olympic-700 text-white font-medium disabled:opacity-50"
        >
          Ask
        </button>
      </form>
    </div>
  );
}
