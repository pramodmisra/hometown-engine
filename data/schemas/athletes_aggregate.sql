-- BigQuery schema for athletes_aggregate.
-- Aggregate-only: no individual athlete records exist past this layer.
-- region_type='state' for the Day 2 baseline; later phases add 'metro', 'county', 'city'.

CREATE SCHEMA IF NOT EXISTS `geminiliveagent-489716.hometown_engine`
  OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `geminiliveagent-489716.hometown_engine.athletes_aggregate` (
  region_id STRING NOT NULL,
  region_name STRING NOT NULL,
  region_type STRING NOT NULL,
  state_code STRING,
  sport STRING NOT NULL,
  is_paralympic BOOL NOT NULL,
  athlete_count INT64 NOT NULL,
  era STRING,
  decade INT64,
  data_source STRING NOT NULL,
  last_updated TIMESTAMP NOT NULL
)
PARTITION BY DATE(last_updated)
CLUSTER BY region_type, is_paralympic, sport
OPTIONS (
  description = "Team USA athletes aggregated by region x sport x Olympic/Paralympic. Built for the Hometown Engine hackathon submission."
);
