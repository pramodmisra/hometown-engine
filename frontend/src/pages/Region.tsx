import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, type RegionResponse } from "../lib/api";
import AthleteSummaryCard from "../components/AthleteSummary";
import Narrative from "../components/Narrative";
import Chat from "../components/Chat";

export default function Region() {
  const { state_code } = useParams<{ state_code: string }>();
  const [data, setData] = useState<RegionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!state_code) return;
    setData(null);
    setError(null);
    api.getRegion(state_code)
      .then((r) => setData(r.data))
      .catch((e) => setError(e?.response?.data?.detail || e.message || "Could not load region."));
  }, [state_code]);

  if (error) {
    return (
      <div className="space-y-3">
        <Link to="/" className="text-sm text-olympic-700 hover:underline">&larr; Back to map</Link>
        <p className="text-sm text-red-600">{error}</p>
      </div>
    );
  }

  if (!data) {
    return <p className="text-sm text-ink-500 animate-pulse">Loading region...</p>;
  }

  const r = data.region;
  return (
    <div className="space-y-8">
      <div>
        <Link to="/" className="text-sm text-olympic-700 hover:underline">&larr; Back to map</Link>
        <h1 className="font-display text-4xl font-semibold mt-2">{r.region_name}</h1>
        <p className="text-sm text-ink-500 mt-1">
          {r.state_code} · {r.region_type}
          {r.population && <> · pop. {r.population.toLocaleString()}</>}
          {r.avg_temp_f != null && <> · avg {Math.round(r.avg_temp_f)}°F</>}
          {r.avg_annual_precip_in != null && <> · ~{Math.round(r.avg_annual_precip_in)}" rain/year</>}
        </p>
      </div>

      <AthleteSummaryCard summary={data.athlete_summary} />

      <Narrative stateCode={r.state_code} />

      <Chat />
    </div>
  );
}
