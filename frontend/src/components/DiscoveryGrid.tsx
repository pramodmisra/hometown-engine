import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Discovery } from "../lib/api";

export default function DiscoveryGrid() {
  const [items, setItems] = useState<Discovery[] | null>(null);

  useEffect(() => {
    api.discover().then((r) => setItems(r.data.discoveries)).catch(() => setItems([]));
  }, []);

  if (items === null) {
    return <p className="text-sm text-ink-500 animate-pulse">Loading surprising hubs...</p>;
  }
  if (items.length === 0) {
    return <p className="text-sm text-ink-500">Discovery Mode is being prepared.</p>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {items.map((d, i) => {
        const isPara = d.is_paralympic;
        const ring = isPara ? "border-paralympic-500" : "border-olympic-500";
        const tag = isPara ? "Paralympic surprise" : "Olympic surprise";
        const tagBg = isPara ? "bg-paralympic-50 text-paralympic-700" : "bg-olympic-50 text-olympic-700";
        return (
          <Link
            key={i}
            to={`/region/${d.state_code}`}
            className={`rounded-xl border-2 ${ring} bg-white p-5 hover:shadow-lg transition-shadow block`}
          >
            <div className="flex items-baseline justify-between mb-2">
              <span className={`text-xs font-medium px-2 py-0.5 rounded ${tagBg}`}>{tag}</span>
              <span className="font-mono text-sm text-ink-500">{d.athlete_count} athletes</span>
            </div>
            <h3 className="font-display font-semibold text-lg">{d.state}</h3>
            <p className="text-sm text-ink-500 mt-0.5">{d.sport}</p>
            <p className="text-sm mt-3 italic text-ink-900">{d.surprise_reason}</p>
            <p className="text-sm mt-2 leading-relaxed text-ink-500">{d.explanation}</p>
          </Link>
        );
      })}
    </div>
  );
}
