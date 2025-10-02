import os
import pathlib
import psycopg
from datetime import datetime, timezone
import time

from myenv import db_config, get_logger

module_name = os.path.splitext(os.path.basename(__file__))[0]
logger = get_logger(module_name)

file_path = '/home/oper/share/monitor-tmp/caenhv-hyptpc.txt'
last_offset = 0

#_________________________________
def main():
  global last_offset
  host = 'caenhv3' # fixed
  while True:
    try:
      with psycopg.connect(**db_config) as conn:
        with conn.cursor() as cur:
          with open(file_path, 'r') as f:
            offset = 0
            for ln, line in enumerate(f, 1):
              offset += 1
              line = line.strip()
              if not line or line.startswith('#') or offset <= last_offset:
                continue
              columns = line.split()
              values = [float(p) for p in columns]
              unixtime = values[0]
              values = {'Cathode': [values[1], values[2], values[3]],
                        'GEM': [values[4], values[5], values[6]],
                        'Gate0': [values[7], values[8], values[9]],
                        'Gate+': [values[10], values[11], values[12]],
                        'Gate-': [values[13], values[14], values[15]],
                        }
              logger.debug(f'{unixtime} {values}')
              for name, val in values.items():
                sql = """
                INSERT INTO caenhv (
                timestamp, ip_address, crate_type,
                channel_name, v0set, vmon, imon ) VALUES (
                to_timestamp(%s), %s, %s, %s, %s, %s, %s )
                ON CONFLICT (timestamp, channel_name) DO NOTHING;
                """
                cur.execute(sql, [unixtime, 'caenhv3', 'SY5527LC', name] + val)
              last_offset = offset
    except Exception as e:
      logger.error(e)
    logger.debug('sleep')
    time.sleep(10)

if __name__ == '__main__':
  main()
