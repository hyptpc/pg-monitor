import os
import subprocess
import psycopg2
from datetime import datetime
import time

from myenv import db_config, get_logger

logger = get_logger('service')
service_list_path = os.path.join(
  os.path.dirname(os.path.abspath(__file__)), 'service_list.txt')

#______________________________________________________________________________
def get_service_status_and_log(service_name):
  # is-active（active/inactive/failed）
  try:
    result = subprocess.run(
      ['systemctl', '--user', 'is-active', service_name],
      stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
    )
    status = result.stdout.strip()
  except Exception:
    status = 'unknown'
  # systemctl status, last log
  try:
    result = subprocess.run(
      ['systemctl', '--user', 'status', service_name],
      stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
    )
    lines = result.stdout.strip().splitlines()
    log_line = ''
    for line in reversed(lines):
      if '●' in line or 'Loaded:' in line or 'Active:' in line:
        continue
      if line.strip():
        log_line = line.strip()
        break
  except Exception:
    log_line = ''
  return status, log_line

def main():
  while True:
    try:
      timestamp = datetime.now()
      with open(service_list_path) as f:
        services = ['pg-updater@'+line.strip() for line in f if line.strip()]
      with psycopg2.connect(**db_config) as conn:
        with conn.cursor() as cur:
          for service in services:
            status, log_line = get_service_status_and_log(service)
            cur.execute("""
              INSERT INTO service (timestamp, name, status, last_log)
              VALUES (%s, %s, %s, %s)
            """, (timestamp, service, status, log_line))
          conn.commit()
    except Exception as e:
      logger.error(e)
    time.sleep(30)

if __name__ == "__main__":
  main()
