import os
import pathlib
import psycopg
from datetime import datetime, timezone
import time

from myenv import db_config, get_logger

module_name = os.path.splitext(os.path.basename(__file__))[0]
logger = get_logger(module_name)

spark_dir = '/home/oper/share/spark'
allow = {".jpg", ".jpeg", ".png"}

def created_ts(p):
  st = p.stat()
  mtime = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
  try:
    out = subprocess.run(["stat", "-c", "%W", str(p)],
                         capture_output=True, text=True, check=True).stdout.strip()
    w = int(out)
    return datetime.fromtimestamp(w, tz=timezone.utc) if w > 0 else mtime
  except Exception:
    return mtime

def run():
  base = pathlib.Path(spark_dir).resolve()
  with psycopg.connect(**db_config) as conn, conn.cursor() as cur:
    for p in sorted(base.glob("*")):
      if not p.is_file() or p.suffix.lower() not in allow:
        continue
      ts = created_ts(p)
      sql = """
      INSERT INTO spark (timestamp, filepath, voltage, threshold)
      VALUES (%s, %s, NULL, NULL)
      ON CONFLICT (timestamp) DO NOTHING;
      """
      cur.execute(sql, (ts, str(p)))
    conn.commit()

def main():
  while True:
    try:
      run()
    except Exception as e:
      logger.error(e)
    time.sleep(20)

if __name__ == '__main__':
  main()
