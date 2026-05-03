"""
Build the regions table from BQ public Census + geo_us_boundaries data.

Output: geminiliveagent-489716.hometown_engine.regions
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
SQL = DATA_DIR / "schemas" / "regions.sql"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("regions")

SA_KEY = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or str(
    Path(__file__).resolve().parents[2] / ".secrets" / "hometown-engine-sa.json"
)


def main() -> int:
    if Path(SA_KEY).exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SA_KEY
    client = bigquery.Client(project=PROJECT, location=LOCATION)
    sql_text = SQL.read_text(encoding="utf-8")
    log.info("running regions DDL ...")
    client.query(sql_text, location=LOCATION).result()
    log.info("regions table built: %s", f"{PROJECT}.{DATASET}.regions")

    df = client.query(
        f"SELECT state_code, region_name, latitude, longitude, population, area_sq_km "
        f"FROM `{PROJECT}.{DATASET}.regions` ORDER BY state_code",
        location=LOCATION,
    ).to_dataframe()
    log.info("regions rows: %d", len(df))
    log.info("\n%s", df.head(15).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
