import { ComposableMap, Geographies, Geography } from "react-simple-maps";
import { useNavigate } from "react-router-dom";
import type { StateSummary } from "../lib/api";

const TOPO_URL =
  "https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json";

const FIPS_TO_STATE_CODE: Record<string, string> = {
  "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO",
  "09": "CT", "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI",
  "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
  "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN",
  "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
  "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
  "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
  "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA",
  "54": "WV", "55": "WI", "56": "WY",
};

export default function USMap({
  states,
  metric = "total",
}: {
  states: StateSummary[];
  metric?: "total" | "olympic" | "paralympic";
}) {
  const navigate = useNavigate();
  const byCode = new Map(states.map((s) => [s.state_code, s]));

  const valueOf = (s?: StateSummary) => {
    if (!s) return 0;
    if (metric === "olympic") return s.olympic_total;
    if (metric === "paralympic") return s.paralympic_total;
    return s.olympic_total + s.paralympic_total;
  };
  const max = Math.max(1, ...states.map((s) => valueOf(s)));

  const colorFor = (val: number) => {
    if (val === 0) return "#f1f5f9";
    const ratio = Math.min(1, val / max);
    // Use a perceptual gradient from light to dark blue, with a hint of orange
    // for the all-paralympic mode so the parity message reads.
    if (metric === "paralympic") {
      const lightness = 92 - ratio * 60;
      return `hsl(33, 90%, ${lightness}%)`;
    }
    const lightness = 92 - ratio * 60;
    return `hsl(217, 80%, ${lightness}%)`;
  };

  return (
    <div className="w-full">
      <ComposableMap projection="geoAlbersUsa" width={980} height={550}>
        <Geographies geography={TOPO_URL}>
          {({ geographies }) =>
            geographies.map((geo) => {
              const fips = String(geo.id).padStart(2, "0");
              const stateCode = FIPS_TO_STATE_CODE[fips];
              const data = byCode.get(stateCode);
              const v = valueOf(data);
              return (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  onClick={() => stateCode && navigate(`/region/${stateCode}`)}
                  fill={colorFor(v)}
                  stroke="#475569"
                  strokeWidth={0.5}
                  style={{
                    default: { outline: "none", cursor: "pointer" },
                    hover: { fill: "#0ea5e9", outline: "none", cursor: "pointer" },
                    pressed: { outline: "none" },
                  }}
                >
                  <title>
                    {stateCode || "Unknown"} — Olympic {data?.olympic_total ?? 0}, Paralympic {data?.paralympic_total ?? 0}
                  </title>
                </Geography>
              );
            })
          }
        </Geographies>
      </ComposableMap>
    </div>
  );
}
