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
        MQV0002(host='192.168.20.14', port=4001, addr=1),
      ]
      timestamp = datetime.now(timezone.utc)
      values = massflow_list[0].info()
      logger.debug(f'{values}')
      with psycopg2.connect(**db_config) as conn:
        with conn.cursor() as cur:
          sql = """
            INSERT INTO {name} ({keys})
            VALUES ({placeholders})
            """.format(
              name=module_name,
              keys=', '.join(values.keys()),
              placeholders=', '.join(['%s'] * len(values))
            )
          cur.execute(sql, list(values.values()))
          conn.commit()
      logger.debug("Logged values at %s", timestamp.isoformat())
    except Exception as e:
      logger.error(e)
    time.sleep(60)

#______________________________________________________________________________
if __name__ == '__main__':
  main()
