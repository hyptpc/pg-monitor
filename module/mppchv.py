"""Import MPPC HV monitor data from raspi-mppchv SQLite snapshots into PostgreSQL.

raspi-mppchv (https://github.com/hyptpc/raspi-mppchv) runs on raspi1/raspi2 and its
sync_db.sh copies measurements_<suffix>.db to monitor-tmp every few seconds
(atomic replace).  Each suffix is one controller, e.g. raspi1_2026Nov or
BHT_BLCVth_2026Nov; the trailing _<YYYY><Mon> is dropped to get a stable
controller name.  Only files updated within ACTIVE_SEC are read.
"""
import glob
import os
import re
import sqlite3
import time
from contextlib import closing
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import psycopg2
from psycopg2.extras import execute_values

from myenv import db_config, get_logger

logger = get_logger('mppchv')

DB_DIR = '/home/oper/share/monitor-tmp'
PATTERN = 'measurements_*.db'
INTERVAL = 10              # seconds between import cycles
ACTIVE_SEC = 3600          # ignore snapshots not updated within this time
BACKFILL = timedelta(days=30)  # first import of a controller goes back at most this far
BATCH = 5000
TZ = ZoneInfo('Asia/Tokyo')  # raspi-mppchv stores naive local time (datetime.now())

COLS = ('timestamp', 'port_id', 'voltage', 'current', 'is_hv_on', 'status_raw', 'temperature',
        'is_overcurrent_protection_active', 'is_current_out_of_spec',
        'is_temp_sensor_connected', 'is_temp_in_range', 'is_temp_correction_enabled')

INSERT = """
INSERT INTO mppchv (timestamp, controller, port, vmon, imon, hvon, status_raw, temp,
                    overcurrent, current_out_of_spec, temp_sensor, temp_in_range, temp_correction)
VALUES %s
ON CONFLICT (controller, port, timestamp) DO NOTHING
"""

#______________________________________________________________________________
def controller_name(path):
  suffix = os.path.basename(path)[len('measurements_'):-len('.db')]
  return re.sub(r'_\d{4}[A-Za-z]+$', '', suffix) or suffix

#______________________________________________________________________________
def to_bool(v):
  return None if v is None else bool(v)

#______________________________________________________________________________
def read_rows(path, controller, since):
  """Rows newer than `since` (naive local time string) from one snapshot."""
  uri = 'file:' + path + '?mode=ro'
  with closing(sqlite3.connect(uri, uri=True, timeout=5)) as src:
    cur = src.execute(f"SELECT {', '.join(COLS)} FROM measurements WHERE timestamp > ? "
                      "ORDER BY timestamp", (since,))
    for r in cur:
      ts = datetime.fromisoformat(r[0]).replace(tzinfo=TZ)
      yield (ts, controller, r[1], r[2], r[3], to_bool(r[4]), r[5], r[6],
             to_bool(r[7]), to_bool(r[8]), to_bool(r[9]), to_bool(r[10]), to_bool(r[11]))

#______________________________________________________________________________
def last_timestamp(conn, controller):
  with conn.cursor() as cur:
    cur.execute('SELECT max(timestamp) FROM mppchv WHERE controller = %s', (controller,))
    ts = cur.fetchone()[0]
  if ts is None:
    ts = datetime.now(TZ) - BACKFILL
  return ts.astimezone(TZ).replace(tzinfo=None).isoformat(sep=' ')

#______________________________________________________________________________
def import_once(conn, last):
  now = time.time()
  for path in sorted(glob.glob(os.path.join(DB_DIR, PATTERN))):
    try:
      if now - os.path.getmtime(path) > ACTIVE_SEC:
        continue
    except FileNotFoundError:
      continue  # replaced between glob and stat
    controller = controller_name(path)
    if controller not in last:
      last[controller] = last_timestamp(conn, controller)
      logger.info(f'{controller}: importing {os.path.basename(path)} since {last[controller]}')
    rows = list(read_rows(path, controller, last[controller]))
    for i in range(0, len(rows), BATCH):
      with conn.cursor() as cur:
        execute_values(cur, INSERT, rows[i:i + BATCH])
      conn.commit()
    if rows:
      last[controller] = rows[-1][0].replace(tzinfo=None).isoformat(sep=' ')
      logger.debug(f'{controller}: {len(rows)} rows')

#______________________________________________________________________________
def main():
  conn = None
  last = {}
  while True:
    try:
      if conn is None or conn.closed:
        conn = psycopg2.connect(**db_config)
        last = {}
      import_once(conn, last)
    except psycopg2.Error as e:
      logger.error(f'database error: {e}')
      try:
        conn.close()
      except Exception:
        pass
      conn = None
    except Exception as e:
      logger.error(f'{type(e).__name__}: {e}')
    time.sleep(INTERVAL)

if __name__ == '__main__':
  main()
