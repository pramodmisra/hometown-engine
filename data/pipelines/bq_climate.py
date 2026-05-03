"""
Run the climate.sql DDL+SELECT against BigQuery to build a state-level
climate normals table from NOAA GSOD (1990-2019 window).

Output: geminiliveagent-489716.hometown_engine.climate
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from google.cloud import bigquery

PROJECT = "geminiliveagent-489716"
DATASET = "hometown_engine"
LOCATION = "US"

DATA_DIR = Path(__file__).resolve().parent.parent
SQL = DATA_DIR / "schemas" / "climate.sql"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("climate")

SA_KEY = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or str(
    Path(__file__).resolve().parents[2] / ".secrets" / "hometown-engine-sa.json"
)


def main() -> int:
    if Path(SA_KEY).exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SA_KEY
    client = bigquery.Client(project=PROJECT, location=LOCATION)

    sql_text = SQL.read_text(encoding="utf-8")
    log.info("running climate DDL (NOAA GSOD 1990-2019, ~30-year window) ...")
    job = client.query(sql_text, location=LOCATION)
    job.result()
    log.info("climate table built: %s", f"{PROJECT}.{DATASET}.climate")

    out = client.query(
        f"SELECT state_code, avg_temp_f, avg_diurnal_range_f, avg_annual_precip_in, station_count "
        f"FROM `{PROJECT}.{DATASET}.climate` ORDER BY state_code",
        location=LOCATION,
    ).to_dataframe()
    log.info("climate rows: %d", len(out))
    log.info("\n%s", out.head(20).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
