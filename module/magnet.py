import time
from datetime import datetime, timezone
from epics import caget
import json
import os
import psycopg2
import pytz

from myenv import db_config, get_logger

module_name = os.path.splitext(os.path.basename(__file__))[0]
logger = get_logger(module_name)

magnet_list = [
  # 'AK11D1',
  'AK18D1', 'AH18', 'BSM1',
  'K18Q1', 'K18Q2', 'K18D2', 'K18Q3',
  'K18O1', 'K18Q4', 'K18S1',
  'K18CM1', 'K18CM2', 'K18S2', 'K18Q5', 'K18Q6',
  'K18D3', 'K18BRS3', 'K18BRQ7',
  'K18BRD4', 'K18BRQ8', 'K18BRD5',
  # 'DORA'
]

#______________________________________________________________________________
def main():
  while True:
    try:
      timestamp = datetime.now(pytz.timezone('Asia/Tokyo'))
      values = {}
      for name in magnet_list:
        try:
          cset = caget(f'HDPS:{name}:CSET')
          cmon = caget(f'HDPS:{name}:CMON')
          pol  = caget(f'HDPS:{name}:POL', as_string=True).lower()
          values[name] = {'cset': cset, 'cmon': cmon, 'pol': pol}
        except Exception as e:
          logger.warning(f'Failed to get {name}: {e}')
      with psycopg2.connect(**db_config) as conn:
        with conn.cursor() as cur:
          sql = f'INSERT INTO {module_name} (timestamp, magnet_data) VALUES (%s, %s)'
          cur.execute(sql, (timestamp, json.dumps(values)))
        logger.debug("Logged %d magnets at %s", len(values), timestamp.isoformat())
    except Exception as e:
      logger.error(e)
    time.sleep(30)

#______________________________________________________________________________
if __name__ == '__main__':
  main()
