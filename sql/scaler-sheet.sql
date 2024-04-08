WITH latest_spill AS (
  SELECT channel, name, value,
    ROW_NUMBER() OVER (PARTITION BY channel ORDER BY timestamp DESC) AS rownum
    FROM scaler
    WHERE trigger = 'Spill On' AND name != '-'
),
avg_tm_value AS (
  SELECT AVG(value) AS tm_avg_value
  FROM latest_spill
  WHERE name = 'TM' AND rownum <= 10
)
SELECT ls.channel, ls.name,
       ROUND(AVG(ls.value)::numeric, 0) AS avg_value,
       ROUND(AVG(ls.value) / atm.tm_avg_value * 1e6, 0) AS normalized_by_tm
FROM latest_spill ls
CROSS JOIN avg_tm_value atm
WHERE ls.rownum <= 10
GROUP BY ls.channel, ls.name, atm.tm_avg_value
ORDER BY ls.channel;
