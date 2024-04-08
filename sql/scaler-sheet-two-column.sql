WITH latest_spill AS (
  SELECT
       channel,
       -- CASE WHEN name = '-' THEN Null ELSE channel END AS channel,
         CASE WHEN name = '-' THEN Null ELSE name END AS name,
         CASE WHEN name = '-' THEN Null ELSE value END AS value,
         -- name,
         -- value,
    ROW_NUMBER() OVER (PARTITION BY channel ORDER BY timestamp DESC) AS rownum
    FROM scaler
    WHERE trigger = 'Spill On' -- AND name != '-'
          AND timestamp >= NOW() - INTERVAL '2 day'
),
avg_tm_value AS (
  SELECT AVG(value) AS tm_avg_value
  FROM latest_spill
  WHERE name = 'TM' AND rownum <= 10
),
first_half AS (
  SELECT ROW_NUMBER() OVER (ORDER BY channel) AS rownum,
       ls.channel, ls.name,
       ROUND(AVG(ls.value)::numeric, 0) AS avg_value,
       ROUND(AVG(ls.value) / atm.tm_avg_value * 1e6, 0) AS normalized_by_tm
  FROM latest_spill ls
  CROSS JOIN avg_tm_value atm
  WHERE ls.rownum <= 10 AND ls.channel < 32
  GROUP BY ls.channel, ls.name, atm.tm_avg_value
  ORDER BY ls.channel
),
second_half AS (
  SELECT ROW_NUMBER() OVER (ORDER BY channel) AS rownum,
       ls.channel, ls.name,
       ROUND(AVG(ls.value)::numeric, 0) AS avg_value,
       ROUND(AVG(ls.value) / atm.tm_avg_value * 1e6, 0) AS normalized_by_tm
  FROM latest_spill ls
  CROSS JOIN avg_tm_value atm
  WHERE ls.rownum <= 10 AND ls.channel >= 32
  GROUP BY ls.channel, ls.name, atm.tm_avg_value
  ORDER BY ls.channel
)
SELECT
  fh.channel,
  fh.name,
  fh.avg_value,
  fh.normalized_by_tm,
  sh.channel,
  sh.name,
  sh.avg_value,
  sh.normalized_by_tm
FROM first_half fh
JOIN second_half sh ON fh.rownum = sh.rownum
;
