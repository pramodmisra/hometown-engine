"""
BigQuery loader for athletes_aggregate.

Reads:    data/processed/athletes_aggregate.parquet
Loads:    geminiliveagent-489716.hometown_engine.athletes_aggregate

Conforms to the schema in data/schemas/athletes_aggregate.sql:
  region_id STRING (state code for Day 2)
  region_name STRING (state name)
  region_type STRING ('state' for Day 2 baseline)
  state_code STRING
  sport STRING
  is_paralympic BOOL
  athlete_count INT64
  era STRING NULL
  decade INT64 NULL
  data_source STRING
  last_updated TIMESTAMP
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from google.cloud import bigquery

DATA_DIR = Path(__file__).resolve().parent.parent
PROCESSED = DATA_DIR / "processed"
PARQUET = PROCESSED / "athletes_aggregate.parquet"
SCHEMA_SQL = DATA_DIR / "schemas" / "athletes_aggregate.sql"

PROJECT = "geminiliveagent-489716"
DATASET = "hometown_engine"
TABLE = "athletes_aggregate"
LOCATION = "US"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("bq_load")

SA_KEY = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or str(
    Path(__file__).resolve().parents[2] / ".secrets" / "hometown-engine-sa.json"
)


def get_client() -> bigquery.Client:
    if Path(SA_KEY).exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SA_KEY
        log.info("using service account key: %s", SA_KEY)
    return bigquery.Client(project=PROJECT, location=LOCATION)


def ensure_dataset(client: bigquery.Client) -> None:
    ds_ref = bigquery.Dataset(f"{PROJECT}.{DATASET}")
    ds_ref.location = LOCATION
    ds_ref.description = "Hometown Engine — Team USA aggregate data, hackathon submission."
    client.create_dataset(ds_ref, exists_ok=True)
    log.info("dataset ensured: %s.%s (%s)", PROJECT, DATASET, LOCATION)


def ensure_table(client: bigquery.Client) -> None:
    schema = [
        bigquery.SchemaField("region_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("region_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("region_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("state_code", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("sport", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("is_paralympic", "BOOL", mode="REQUIRED"),
        bigquery.SchemaField("athlete_count", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("era", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("decade", "INT64", mode="NULLABLE"),
        bigquery.SchemaField("data_source", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("last_updated", "TIMESTAMP", mode="REQUIRED"),
    ]
    table_id = f"{PROJECT}.{DATASET}.{TABLE}"
    table = bigquery.Table(table_id, schema=schema)
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY, field="last_updated",
    )
    table.clustering_fields = ["region_type", "is_paralympic", "sport"]
    client.create_table(table, exists_ok=True)
    log.info("table ensured: %s", table_id)


def load_aggregate(client: bigquery.Client) -> int:
    if not PARQUET.exists():
        raise FileNotFoundError(f"missing {PARQUET}; run aggregate.py first")
    df = pd.read_parquet(PARQUET)
    log.info("loaded parquet: %d rows", len(df))

    out = pd.DataFrame({
        "region_id": df["state_code"].astype(str),
        "region_name": df["state"].astype(str),
        "region_type": "state",
        "state_code": df["state_code"].astype(str),
        "sport": df["sport"].astype(str),
        "is_paralympic": df["is_paralympic"].astype(bool),
        "athlete_count": df["athlete_count"].astype("int64"),
        "era": pd.Series([None] * len(df), dtype="object"),
        "decade": pd.Series([pd.NA] * len(df), dtype="Int64"),
        "data_source": df["data_source"].astype(str),
        "last_updated": pd.Timestamp(datetime.now(tz=timezone.utc)),
    })

    table_id = f"{PROJECT}.{DATASET}.{TABLE}"
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        schema=[
            bigquery.SchemaField("region_id", "STRING"),
            bigquery.SchemaField("region_name", "STRING"),
            bigquery.SchemaField("region_type", "STRING"),
            bigquery.SchemaField("state_code", "STRING"),
            bigquery.SchemaField("sport", "STRING"),
            bigquery.SchemaField("is_paralympic", "BOOL"),
            bigquery.SchemaField("athlete_count", "INT64"),
            bigquery.SchemaField("era", "STRING"),
            bigquery.SchemaField("decade", "INT64"),
            bigquery.SchemaField("data_source", "STRING"),
            bigquery.SchemaField("last_updated", "TIMESTAMP"),
        ],
    )
    job = client.load_table_from_dataframe(out, table_id, job_config=job_config, location=LOCATION)
    job.result()
    log.info("loaded %d rows into %s", job.output_rows, table_id)
    return int(job.output_rows or 0)


def main() -> int:
    client = get_client()
    ensure_dataset(client)
    ensure_table(client)
    n = load_aggregate(client)
    sample = client.query(
        f"SELECT region_name, sport, is_paralympic, athlete_count "
        f"FROM `{PROJECT}.{DATASET}.{TABLE}` "
        f"ORDER BY athlete_count DESC LIMIT 10",
        location=LOCATION,
    ).to_dataframe()
    log.info("top 10 (state, sport) by count:")
    for _, row in sample.iterrows():
        kind = "Para" if row["is_paralympic"] else "Oly "
        log.info("  %s %-25s %-22s %d", kind, row["region_name"], row["sport"], row["athlete_count"])
    log.info("done. loaded %d rows.", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
