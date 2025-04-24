import time
from datetime import datetime, timezone
from epics import caget
import psycopg2
import pytz
import logging

from myenv import db_config, get_logger

logger = get_logger('pps')

pv_map = {
  'HDPPS:K18:CNTR1_1S': 'k18_cntr1_1s',
  'HDPPS:K18:CNTR1_INTG_HR': 'k18_cntr1_intg_hr',
  'HDPPS:K18BR:CNTR1_1S': 'k18br_cntr1_1s',
  'HDPPS:K18BR:CNTR1_INTG_HR': 'k18br_cntr1_intg_hr',
  'RADHD:ORG0201G:VAL:LEVEL': 'org0201g',
  'RADHD:ORG0201N:VAL:LEVEL': 'org0201n',
  'RADHD:ORG0202G:VAL:LEVEL': 'org0202g',
  'RADHD:ORG0202N:VAL:LEVEL': 'org0202n',
}

#_________________________________
def main():
  while True:
    try:
      timestamp = datetime.now(pytz.timezone('Asia/Tokyo'))
      values = {col: caget(pv) for pv, col in pv_map.items()}
      with psycopg2.connect(**db_config) as conn:
        with conn.cursor() as cur:
          sql = f"""
            INSERT INTO pps (timestamp, {', '.join(values.keys())})
            VALUES (%s, {', '.join(["%s"] * len(values))})
            """
          cur.execute(sql, [timestamp] + list(values.values()))
          conn.commit()
      logger.debug("Logged values at %s", timestamp.isoformat())
    except Exception as e:
      logger.error(e)
    time.sleep(10)

if __name__ == '__main__':
  main()
