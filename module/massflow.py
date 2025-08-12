from datetime import datetime, timezone
from epics import caget
import logging
import os
import psycopg2
import time

from myenv import db_config, get_logger

from mqv0002 import MQV0002

module_name = os.path.splitext(os.path.basename(__file__))[0]
logger = get_logger(module_name)

#______________________________________________________________________________
def main():
  while True:
    try:
      massflow_list = [
        MQV0002(host='192.168.20.14', port=4001, addr=1), # nport1 - input
        MQV0002(host='192.168.20.17', port=4196, addr=1), # waveshare1 - output
      ]
      timestamp = datetime.now(timezone.utc)
      rows = []
      for mf in massflow_list:
        try:
          values = mf.info()
          values["timestamp"] = timestamp
          rows.append(values)
          logger.debug(f'{mf.host}:{mf.port}/addr{getattr(mf,"addr",None)} -> {values}')
        except Exception as de:
          logger.error(f'read failed: {mf}: {de}')
      if not rows:
        logger.warning('no data rows collected; skip insert')
      else:
        keys = list(rows[0].keys())
        placeholders = ', '.join(['%s'] * len(keys))
        sql = f"""
          INSERT INTO {module_name} ({', '.join(keys)})
          VALUES ({placeholders})
        """
        with psycopg2.connect(**db_config) as conn:
          with conn.cursor() as cur:
            cur.executemany(sql, [ [r[k] for k in keys] for r in rows ])
            conn.commit()
        logger.debug("Logged %d rows at %s", len(rows), timestamp.isoformat())
    except Exception as e:
      logger.error(e)
    time.sleep(60)

#______________________________________________________________________________
if __name__ == '__main__':
  main()
