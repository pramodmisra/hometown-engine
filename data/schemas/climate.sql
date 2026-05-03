-- State-level climate baseline derived from NOAA GSOD.
-- 30-year normalish window (1990-2019) keeps it defensible without needing the latest hot tail.

CREATE OR REPLACE TABLE `geminiliveagent-489716.hometown_engine.climate` AS
WITH us_stations AS (
  SELECT
    usaf,
    wban,
    state,
    lat,
    lon,
    elev
  FROM `bigquery-public-data.noaa_gsod.stations`
  WHERE country = 'US'
    AND state IS NOT NULL
    AND state != ''
    AND lat IS NOT NULL
    AND lon IS NOT NULL
),
station_day AS (
  SELECT
    s.state,
    g.stn,
    g.wban,
    EXTRACT(YEAR FROM PARSE_DATE('%Y%m%d', CONCAT(g.year, g.mo, g.da))) AS yr,
    SAFE_CAST(g.temp AS FLOAT64) AS temp_f,
    SAFE_CAST(g.max AS FLOAT64) AS max_f,
    SAFE_CAST(g.min AS FLOAT64) AS min_f,
    SAFE_CAST(g.prcp AS FLOAT64) AS prcp_in
  FROM `bigquery-public-data.noaa_gsod.gsod*` g
  JOIN us_stations s ON g.stn = s.usaf AND g.wban = s.wban
  WHERE _TABLE_SUFFIX BETWEEN '1990' AND '2019'
),
station_year AS (
  SELECT
    state, stn, wban, yr,
    AVG(IF(temp_f < 200, temp_f, NULL)) AS avg_temp_f,
    AVG(IF(max_f < 200, max_f, NULL)) AS avg_max_f,
    AVG(IF(min_f > -200 AND min_f < 200, min_f, NULL)) AS avg_min_f,
    -- Annualize using mean daily rain x 365 to handle stations with partial-year records
    AVG(IF(prcp_in < 30, prcp_in, NULL)) * 365.0 AS annual_precip_in,
    COUNT(IF(prcp_in < 30, 1, NULL)) AS prcp_days
  FROM station_day
  GROUP BY state, stn, wban, yr
  HAVING prcp_days >= 100
)
SELECT
  state AS state_code,
  ROUND(AVG(avg_temp_f), 2) AS avg_temp_f,
  ROUND(AVG(avg_max_f), 2) AS avg_max_f,
  ROUND(AVG(avg_min_f), 2) AS avg_min_f,
  ROUND(AVG(avg_max_f) - AVG(avg_min_f), 2) AS avg_diurnal_range_f,
  ROUND(AVG(annual_precip_in), 2) AS avg_annual_precip_in,
  COUNT(DISTINCT CONCAT(stn, '-', wban)) AS station_count,
  COUNT(DISTINCT yr) AS year_count,
  CURRENT_TIMESTAMP() AS last_updated
FROM station_year
GROUP BY state_code
HAVING station_count >= 3 AND year_count >= 10;
