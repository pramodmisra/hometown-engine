"""BigQuery wrapper. Aggregate-only outputs by design — no individual athlete records."""
from __future__ import annotations

import logging
from functools import lru_cache

from google.cloud import bigquery

from app.config import settings

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_client() -> bigquery.Client:
    return bigquery.Client(project=settings.gcp_project, location=settings.bq_location)


def query_region(state_code: str) -> dict | None:
    """Return region metadata + climate for one state. Returns None if missing."""
    sql = f"""
    SELECT
      r.region_id, r.region_name, r.region_type, r.state_code,
      r.fips, r.latitude, r.longitude, r.population, r.area_sq_km,
      c.avg_temp_f, c.avg_diurnal_range_f, c.avg_annual_precip_in
    FROM `{settings.gcp_project}.{settings.bq_dataset}.regions` r
    LEFT JOIN `{settings.gcp_project}.{settings.bq_dataset}.climate` c
      ON r.state_code = c.state_code
    WHERE r.state_code = @state_code
    LIMIT 1
    """
    job = get_client().query(
        sql,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("state_code", "STRING", state_code.upper())]
        ),
        location=settings.bq_location,
    )
    rows = list(job.result())
    if not rows:
        return None
    return dict(rows[0].items())


def query_athlete_summary(state_code: str) -> dict:
    """Aggregate athlete counts for one state, split Olympic / Paralympic."""
    sql = f"""
    SELECT sport, is_paralympic, athlete_count
    FROM `{settings.gcp_project}.{settings.bq_dataset}.athletes_aggregate`
    WHERE state_code = @state_code
    ORDER BY athlete_count DESC
    """
    job = get_client().query(
        sql,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("state_code", "STRING", state_code.upper())]
        ),
        location=settings.bq_location,
    )
    olympic_sports: list[dict] = []
    paralympic_sports: list[dict] = []
    olympic_total = 0
    paralympic_total = 0
    for r in job.result():
        item = {"sport": r["sport"], "athlete_count": int(r["athlete_count"])}
        if r["is_paralympic"]:
            paralympic_sports.append(item)
            paralympic_total += item["athlete_count"]
        else:
            olympic_sports.append(item)
            olympic_total += item["athlete_count"]
    return {
        "olympic_total": olympic_total,
        "paralympic_total": paralympic_total,
        "top_olympic_sports": olympic_sports[:10],
        "top_paralympic_sports": paralympic_sports[:10],
    }


def query_all_states_summary() -> list[dict]:
    """For map view: per-state Olympic + Paralympic totals."""
    sql = f"""
    SELECT
      state_code,
      SUM(IF(is_paralympic = FALSE, athlete_count, 0)) AS olympic_total,
      SUM(IF(is_paralympic = TRUE,  athlete_count, 0)) AS paralympic_total
    FROM `{settings.gcp_project}.{settings.bq_dataset}.athletes_aggregate`
    GROUP BY state_code
    ORDER BY state_code
    """
    job = get_client().query(sql, location=settings.bq_location)
    return [
        {
            "state_code": r["state_code"],
            "olympic_total": int(r["olympic_total"]),
            "paralympic_total": int(r["paralympic_total"]),
        }
        for r in job.result()
    ]
