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
  host = 'raspi1' # fixed
  while True:
    try:
      with psycopg2.connect(**db_config) as conn:
        with conn.cursor() as cur:
          file_name='/home/oper/share/monitor-tmp/mppc_monitor_value.txt'
          with open(file_name, 'r') as f:
            reader = csv.reader(f, delimiter="\t")
            headers = next(reader)
            ch_count = (len(headers) - 1) // 6
            if last_offset != 0:
              f.seek(last_offset)
              reader = csv.reader(f, delimiter="\t")
            for row in reader:
              timestamp = datetime.fromisoformat(row[0])
              for ch in range(ch_count):
                base = 1 + ch * 6
                hvon = bool(int(row[base]))
                overcurrent = bool(int(row[base + 1]))
                vmon = float(row[base + 2]) if row[base + 2] != 'None' else None
                vset = float(row[base + 3]) if row[base + 3] != 'None' else None
                imon = float(row[base + 4]) if row[base + 4] != 'None' else None
                temp = float(row[base + 5]) if row[base + 5] != 'None' else None
                logger.debug(f'{timestamp} {host} {ch} {hvon} {overcurrent} {vmon} {vset} {imon} {temp}')
                sql = """
                INSERT INTO mppchv (timestamp, host, channel, hvon, overcurrent, vmon, vset, imon, temp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (timestamp) DO NOTHING
                """
                cur.execute(sql, (timestamp, host, ch, hvon, overcurrent, vmon, vset, imon, temp))
                conn.commit()
            last_offset = f.tell()
    except Exception as e:
      logger.error(e)
    time.sleep(10)

if __name__ == '__main__':
  main()
