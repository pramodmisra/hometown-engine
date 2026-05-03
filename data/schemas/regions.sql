-- State-level regions table: name, FIPS code, centroid, population, area.
-- Sources: bigquery-public-data.geo_us_boundaries.states + census_bureau_acs.state_2020_5yr.

CREATE OR REPLACE TABLE `geminiliveagent-489716.hometown_engine.regions` AS
WITH state_geo AS (
  SELECT
    state AS state_code,
    state_name AS region_name,
    state_fips_code AS fips,
    ST_Y(ST_Centroid(state_geom)) AS latitude,
    ST_X(ST_Centroid(state_geom)) AS longitude,
    ST_Area(state_geom) / 1000000.0 AS area_sq_km
  FROM `bigquery-public-data.geo_us_boundaries.states`
),
state_pop AS (
  SELECT
    geo_id AS fips,
    SUM(total_pop) AS population
  FROM `bigquery-public-data.census_bureau_acs.state_2020_5yr`
  GROUP BY fips
)
SELECT
  g.state_code AS region_id,
  g.region_name,
  'state' AS region_type,
  g.state_code,
  g.fips,
  g.latitude,
  g.longitude,
  CAST(p.population AS INT64) AS population,
  ROUND(g.area_sq_km, 2) AS area_sq_km,
  CURRENT_TIMESTAMP() AS last_updated
FROM state_geo g
LEFT JOIN state_pop p USING (fips)
ORDER BY g.state_code;
