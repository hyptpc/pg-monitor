import time
from datetime import datetime
from zoneinfo import ZoneInfo
import logging
import os
import re

import psycopg

from myenv import db_config, get_logger

module_name = os.path.splitext(os.path.basename(__file__))[0]
logger = get_logger(module_name)

#______________________________________________________________________________
def parse(path):
  timestamp = None
  values = dict()
  with open(path, 'r') as f:
    for line in f:
      line = line.strip()
      if ":" not in line:
        continue
      if line.startswith("Time:"):
        # Example: "Time: 2025/10/19 17:25:20"
        ts_str = line.split("Time:", 1)[1].strip()
        timestamp = datetime.strptime(
          ts_str, "%Y/%m/%d %H:%M:%S").replace(tzinfo=ZoneInfo("Asia/Tokyo"))
        values['timestamp'] = timestamp
        continue
      key, val = line.split(":", 1)
      key = key.strip()
      val = val.strip()
      try:
        if re.fullmatch(r"[+-]?\d+", val):
          val = int(val)
          if val < 2:
            val = bool(val)
        else:
          val = float(val)
      except ValueError:
        val = None
      values[key.lower().replace('/off', '').replace('.', '_')
             .replace('up', '_up').replace('dw', '_dw')] = val
  if timestamp is None:
    raise ValueError('invalid timestamp')
  return values

# ---- DB upsert ----
UPSERT_SQL = """
INSERT INTO target (
    timestamp,
    temp_ref1st, temp_cond_up, temp_cond_dw, temp_tgt_up, temp_tgt_dw, temp_room,
    h2_press, heater_v, vac_cryo, vac_tank, press_diff,
    h2leak_1, h2leak_2, h2leak_3,
    fan_on, ref_on, alert_ybox, alert_gl860, alert_h2leak, alert_user,
    hdexhaust_flow
) VALUES (
    %(timestamp)s,
    %(temp_ref1st)s, %(temp_cond_up)s, %(temp_cond_dw)s, %(temp_tgt_up)s, %(temp_tgt_dw)s, %(temp_room)s,
    %(h2_press)s, %(heater_v)s, %(vac_cryo)s, %(vac_tank)s, %(press_diff)s,
    %(h2leak_1)s, %(h2leak_2)s, %(h2leak_3)s,
    %(fan_on)s, %(ref_on)s, %(alert_ybox)s, %(alert_gl860)s, %(alert_h2leak)s, %(alert_user)s,
    %(hdexhaust_flow)s
)
ON CONFLICT (timestamp) DO UPDATE SET
    temp_ref1st = EXCLUDED.temp_ref1st,
    temp_cond_up = EXCLUDED.temp_cond_up,
    temp_cond_dw = EXCLUDED.temp_cond_dw,
    temp_tgt_up = EXCLUDED.temp_tgt_up,
    temp_tgt_dw = EXCLUDED.temp_tgt_dw,
    temp_room = EXCLUDED.temp_room,
    h2_press = EXCLUDED.h2_press,
    heater_v = EXCLUDED.heater_v,
    vac_cryo = EXCLUDED.vac_cryo,
    vac_tank = EXCLUDED.vac_tank,
    press_diff = EXCLUDED.press_diff,
    h2leak_1 = EXCLUDED.h2leak_1,
    h2leak_2 = EXCLUDED.h2leak_2,
    h2leak_3 = EXCLUDED.h2leak_3,
    fan_on = EXCLUDED.fan_on,
    ref_on = EXCLUDED.ref_on,
    alert_ybox = EXCLUDED.alert_ybox,
    alert_gl860 = EXCLUDED.alert_gl860,
    alert_h2leak = EXCLUDED.alert_h2leak,
    alert_user = EXCLUDED.alert_user,
    hdexhaust_flow = EXCLUDED.hdexhaust_flow
;
"""

#______________________________________________________________________________
def upsert(conn, rec):
  with conn.cursor() as cur:
    cur.execute(UPSERT_SQL, rec)

#______________________________________________________________________________
def main():
  with psycopg.connect(**db_config) as conn:
    conn.autocommit = True
    last_time = None
    while True:
      try:
        rec = parse('/home/oper/share/monitor-tmp/H2tgtPresentStatus.txt')
        if last_time is None or rec['timestamp'] != last_time:
          upsert(conn, rec)
          leak = rec.get('alert_h2leak')
          if leak:
            logger.info(f"detected lh2 leak\n{rec}")
          else:
            logger.debug(f"upsert {rec['timestamp'].isoformat()}")
          last_time = rec['timestamp']
        else:
          logger.debug("no new timestamp; skip")
      except Exception as e:
        logger.error(f"ingest error: {e}")
      time.sleep(10)

#______________________________________________________________________________
if __name__ == "__main__":
  main()
