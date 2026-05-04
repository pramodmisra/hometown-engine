import type { AthleteSummary } from "../lib/api";

function SportList({
  title,
  total,
  sports,
  variant,
}: {
  title: string;
  total: number;
  sports: { sport: string; athlete_count: number }[];
  variant: "olympic" | "paralympic";
}) {
  const colorClass =
    variant === "olympic"
      ? "border-olympic-500 bg-olympic-50"
      : "border-paralympic-500 bg-paralympic-50";
  const accentClass = variant === "olympic" ? "text-olympic-700" : "text-paralympic-700";
  return (
    <div className={`rounded-xl border-2 ${colorClass} p-5`}>
      <div className="flex items-baseline justify-between">
        <h3 className={`font-display font-semibold text-base ${accentClass}`}>{title}</h3>
        <span className={`font-display text-3xl font-semibold ${accentClass}`}>{total}</span>
      </div>
      <p className="text-xs text-ink-500 mt-1 mb-3">athletes from this region</p>
      {sports.length === 0 ? (
        <p className="text-sm text-ink-500 italic">No data in this aggregate.</p>
      ) : (
        <ul className="space-y-1.5">
          {sports.slice(0, 8).map((s) => (
            <li key={s.sport} className="flex items-center justify-between text-sm">
              <span>{s.sport}</span>
              <span className="font-mono text-ink-500">{s.athlete_count}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function AthleteSummaryCard({ summary }: { summary: AthleteSummary }) {
  return (
    // Equal-weight grid: each column sized identically so Olympic and Paralympic share visual weight.
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <SportList
        title="Olympic representation"
        total={summary.olympic_total}
        sports={summary.top_olympic_sports}
        variant="olympic"
      />
      <SportList
        title="Paralympic representation"
        total={summary.paralympic_total}
        sports={summary.top_paralympic_sports}
        variant="paralympic"
      />
    </div>
  );
}
