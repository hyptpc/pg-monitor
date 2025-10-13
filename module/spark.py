from datetime import datetime, timezone
import os
import pathlib
import psycopg
import requests
import time
import signal, sys, atexit, threading

from myenv import db_config, get_logger

import mdo3032

module_name = os.path.splitext(os.path.basename(__file__))[0]
logger = get_logger(module_name)

spark_dir = mdo3032.SAVE_DIR
allow = {".jpg", ".jpeg", ".png"}

WEBHOOK_URL = 'https://discord.com/api/webhooks/1424709205130088468/FAWcP01LDWF7xi1ETLs93aOEeTepHB4yVoZ0awPFUEpE8DidTQ2KqdqzFxPANaeKQDGD' # E72 spark

shutdown = threading.Event()

#______________________________________________________________________________
def _handler(signum, frame):
  shutdown.set()
  mdo3032.finalize()
  sys.exit(0)

#______________________________________________________________________________
def run():
  ts, out, vth = mdo3032.run()
  with psycopg.connect(**db_config) as conn, conn.cursor() as cur:
    sql = """
    INSERT INTO spark (timestamp, filepath, threshold)
    VALUES (to_timestamp(%s), %s, %s)
    ON CONFLICT (timestamp) DO NOTHING;
    """
    cur.execute(sql, (ts, str(out.resolve()), vth))

    vmon = dict()
    imon = dict()
    msg = ''
    for key in ['Cathode', 'GEM',]:
      sql = f"""
      SELECT timestamp, vmon, imon from caenhv
      where channel_name = '{key}' and ip_address = 'caenhv3'
      order by timestamp desc limit 1
      """
      cur.execute(sql)
      key = key[:3].lower()
      row = cur.fetchone()
      if row is not None and len(row) == 3:
        vmon[key] = f"{row[1]:.0f} V"
        imon[key] = f"{row[2]:.2f} uA"
      else:
        vmon[key] = None
        imon[key] = None
      msg += f'\nv{key} = {vmon[key]}, i{key} = {imon[key]}'
    send_image(out, f"image: `{out}`{msg}")
    msg = msg.replace('\n', ', ')
    logger.info(f"image: {out}{msg}")

#______________________________________________________________________________
def send_image(file_path, content="Captured image", wait=True):
  """Send the saved image to Discord webhook (best-effort)."""
  params = {"wait": "true"} if wait else None
  data = {"content": content}
  try:
    with open(file_path, "rb") as f:
      files = {"file": (pathlib.Path(file_path).name, f)}
      requests.post(WEBHOOK_URL, params=params,
                    data=data, files=files, timeout=20)
  except Exception as e:
    logger.error(f"Webhook post failed: {e}")

#______________________________________________________________________________
def main():
  atexit.register(mdo3032.finalize)
  for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
    signal.signal(sig, _handler)

  try:
    mdo3032.initialize()
    while not shutdown.is_set():
      try:
        run()
      except Exception as e:
        logger.error(e)
      time.sleep(20)
  except Exception as e:
    logger.error(e)

#______________________________________________________________________________
if __name__ == '__main__':
  main()
