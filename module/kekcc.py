"""Store the KEKCC HSM rawdata listing in PostgreSQL.

The listing is written every 5 min by data-transfer/jparc-k18br/ls-kekcc.sh
(crontab of hayakawa) as `ls -la --time-style=+%Y-%m-%dT%H:%M:%S`.
"""
from datetime import datetime
import os
import re
import time
from zoneinfo import ZoneInfo

import psycopg2

from myenv import db_config, get_logger

module_name = os.path.splitext(os.path.basename(__file__))[0]
logger = get_logger(module_name)

list_path = '/mnt/nvme0/share/monitor-tmp/ls-kekcc.txt'
INTERVAL = 30  # seconds between checks of list_path
JST = ZoneInfo('Asia/Tokyo')

line_re = re.compile(
  r'^(\S{10})\s+\d+\s+\S+\s+\S+\s+(\d+)\s+'
  r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s+run(\d+)\.dat$')

#______________________________________________________________________________
def parse_list(path):
  files = {}
  with open(path) as f:
    for line in f:
      m = line_re.match(line.rstrip('\n'))
      if not m:
        continue
      files[int(m[4])] = (
        int(m[2]),
        datetime.fromisoformat(m[3]).replace(tzinfo=JST),
        'w' not in m[1],
      )
  return files

#______________________________________________________________________________
def update_db(files, listed_at, cache):
  conn = psycopg2.connect(**db_config)
  try:
    with conn, conn.cursor() as cur:
      for run, (size, mtime, readonly) in files.items():
        if cache.get(run) == (size, mtime, readonly):
          continue
        cur.execute("""
          INSERT INTO kekcc_rawdata (run_number, size_bytes, mtime, readonly)
          VALUES (%s, %s, %s, %s)
          ON CONFLICT (run_number) DO UPDATE SET
            timestamp = now(),
            size_bytes = EXCLUDED.size_bytes,
            mtime = EXCLUDED.mtime,
            readonly = EXCLUDED.readonly;
        """, (run, size, mtime, readonly))
      cur.execute("DELETE FROM kekcc_rawdata WHERE NOT (run_number = ANY(%s))",
                  (list(files),))
      cur.execute("""
        INSERT INTO kekcc_status (id, listed_at, n_files) VALUES (1, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
          timestamp = now(),
          listed_at = EXCLUDED.listed_at,
          n_files = EXCLUDED.n_files;
      """, (listed_at, len(files)))
  finally:
    conn.close()

#______________________________________________________________________________
def main():
  logger.info('start')
  cache = {}
  last_mtime = None
  while True:
    try:
      st = os.stat(list_path)
      if st.st_mtime != last_mtime:
        files = parse_list(list_path)
        if files:
          listed_at = datetime.fromtimestamp(st.st_mtime, JST)
          update_db(files, listed_at, cache)
          cache = files
          last_mtime = st.st_mtime
        else:
          logger.warning(f'no run files in {list_path}')
    except Exception as e:
      logger.error(e)
    time.sleep(INTERVAL)

#______________________________________________________________________________
if __name__ == '__main__':
  main()
