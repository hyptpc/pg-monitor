import csv
import time
from datetime import datetime, timezone
from epics import caget
import os
import psycopg2
import logging

from myenv import db_config, get_logger

module_name = os.path.splitext(os.path.basename(__file__))[0]
logger = get_logger(module_name)

last_offset = 0

#_________________________________
def main():
  global last_offset
  while True:
    file_name='/home/oper/share/monitor-tmp/mppc_monitor_value.txt'
    with open(file_name, 'r') as f:
      reader = csv.reader(f, delimiter="\t")
      headers = next(reader)
      ch_count = (len(headers) - 1) // 6
      for row in reader:
        timestamp = datetime.fromisoformat(row[0])
        for ch in range(ch_count):
          base = 1 + ch * 6
          hvon = row[base]
          overcurrent = row[base + 1]
          vmon = row[base + 2]
          vset = row[base + 3]
          curr = row[base + 4]
          temp = row[base + 5]
          logger.info(f'{timestamp} {ch} {hvon} {overcurrent} {vmon} {vset} {curr} {temp}')

    try:
      # timestamp = datetime.now(timezone.utc)
      # values = {col: caget(pv) for pv, col in PV_MAP.items()}
      # with psycopg2.connect(**db_config) as conn:
      #   with conn.cursor() as cur:
      #     sql = """
      #       INSERT INTO ess (timestamp, {columns})
      #       VALUES (%s, {placeholders})
      #       """.format(
      #         columns=", ".join(values.keys()),
      #         placeholders=", ".join(["%s"] * len(values))
      #       )
      #     cur.execute(sql, [timestamp] + list(values.values()))
      #     conn.commit()
      # logger.debug("Logged values at %s", timestamp.isoformat())
      read()
    except Exception as e:
      logger.error("Error during logging: %s", e)
    time.sleep(10)

if __name__ == '__main__':
  main()
