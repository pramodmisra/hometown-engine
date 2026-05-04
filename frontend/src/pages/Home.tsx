import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type StateSummary } from "../lib/api";
import { zipToState } from "../lib/zip-to-state";
import USMap from "../components/USMap";
import DiscoveryGrid from "../components/DiscoveryGrid";

export default function Home() {
  const [states, setStates] = useState<StateSummary[] | null>(null);
  const [zip, setZip] = useState("");
  const [zipError, setZipError] = useState<string | null>(null);
  const [metric, setMetric] = useState<"total" | "olympic" | "paralympic">("total");
  const navigate = useNavigate();

  useEffect(() => {
    api.listStates().then((r) => setStates(r.data.states)).catch(() => setStates([]));
  }, []);

  const onZipSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const code = zipToState(zip);
    if (!code) {
      setZipError("Please enter a valid 5-digit US ZIP code.");
      return;
    }
    setZipError(null);
    navigate(`/region/${code}`);
  };

  return (
    <div className="space-y-12">
      <section className="space-y-4">
        <h1 className="font-display text-4xl md:text-5xl font-semibold tracking-tight">
          Where could Team USA come from?
        </h1>
        <p className="text-lg text-ink-500 max-w-3xl">
          Enter a US ZIP code or click any state to see how many Olympians and Paralympians have come from that region,
          which sports cluster there, and what local conditions <em>could help foster</em> athletic excellence.
          Olympic and Paralympic representation are shown with equal weight.
        </p>

        <form onSubmit={onZipSubmit} className="flex flex-wrap gap-3 items-center">
          <input
            value={zip}
            onChange={(e) => setZip(e.target.value)}
            placeholder="Try your ZIP — e.g. 30022"
            inputMode="numeric"
            pattern="[0-9]*"
            maxLength={5}
            className="px-4 py-3 rounded-lg border border-ink-200 w-72 focus:outline-none focus:ring-2 focus:ring-olympic-500"
          />
          <button type="submit" className="px-5 py-3 rounded-lg bg-olympic-700 text-white font-medium">
            Show my hometown
          </button>
          {zipError && <span className="text-sm text-red-600">{zipError}</span>}
        </form>
      </section>

      <section className="space-y-3">
        <div className="flex items-baseline justify-between flex-wrap gap-3">
          <div>
            <h2 className="font-display text-2xl font-semibold">All 50 states + DC</h2>
            <p className="text-sm text-ink-500">Click any state for a detail view.</p>
          </div>
          <div className="flex gap-2 text-sm">
            {(["total", "olympic", "paralympic"] as const).map((m) => (
              <button
                key={m}
                onClick={() => setMetric(m)}
                className={`px-3 py-1.5 rounded-full border ${
                  metric === m
                    ? m === "paralympic"
                      ? "bg-paralympic-500 text-white border-paralympic-500"
                      : "bg-olympic-700 text-white border-olympic-700"
                    : "border-ink-200 text-ink-500"
                }`}
              >
                {m === "total" ? "Combined" : m === "olympic" ? "Olympic" : "Paralympic"}
              </button>
            ))}
          </div>
        </div>
        {states ? (
          <div className="rounded-2xl border border-ink-200 bg-white p-3 overflow-x-auto">
            <USMap states={states} metric={metric} />
          </div>
        ) : (
          <p className="text-sm text-ink-500 animate-pulse">Loading map...</p>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="font-display text-2xl font-semibold">Surprising hubs</h2>
        <p className="text-sm text-ink-500 max-w-3xl">
          Gemini reads the full aggregate and identifies five regions whose representation in a particular sport
          may be associated with unexpected local conditions. At least two are Paralympic-focused.
        </p>
        <DiscoveryGrid />
      </section>
    </div>
  );
}
