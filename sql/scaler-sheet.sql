WITH latest_spill AS (
  SELECT timestamp, value
  FROM scaler
  -- WHERE trigger = 'Spill On'
  ORDER BY timestamp DESC
  LIMIT 10
),
avg_tm_value AS (
  SELECT AVG(value[2]) AS tm_avg_value
  FROM latest_spill
)
SELECT ls.timestamp,
       UNNEST(ls.value)
       -- ROUND(AVG(UNNEST(ls.value))::numeric, 0) AS avg_value,
       -- ROUND(AVG(UNNEST(ls.value)) / atm.tm_avg_value * 1e6, 0) AS normalized_by_tm
FROM latest_spill ls
CROSS JOIN avg_tm_value atm
