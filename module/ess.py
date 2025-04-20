import time
from datetime import datetime, timezone
from epics import caget
import psycopg2
import logging

from myenv import db_config, get_logger

logger = get_logger('ess')

PV_MAP = {
  'HDESS:K18_ESS1:NEG_VSET': 'neg_vset1',
  'HDESS:K18_ESS1:POS_VSET': 'pos_vset1',
  'HDESS:K18_ESS1:NEG_VMON': 'neg_vmon1',
  'HDESS:K18_ESS1:POS_VMON': 'pos_vmon1',
  'HDESS:K18_ESS1:NEG_IMON': 'neg_imon1',
  'HDESS:K18_ESS1:POS_IMON': 'pos_imon1',
  'HDESS:K18_ESS1:CCG_PMON': 'ccg_pmon1',
  'HDESS:K18_ESS2:NEG_VSET': 'neg_vset2',
  'HDESS:K18_ESS2:POS_VSET': 'pos_vset2',
  'HDESS:K18_ESS2:NEG_VMON': 'neg_vmon2',
  'HDESS:K18_ESS2:POS_VMON': 'pos_vmon2',
  'HDESS:K18_ESS2:NEG_IMON': 'neg_imon2',
  'HDESS:K18_ESS2:POS_IMON': 'pos_imon2',
  'HDESS:K18_ESS2:CCG_PMON': 'ccg_pmon2'
}

#_________________________________
def main():
  while True:
    try:
      timestamp = datetime.now(timezone.utc)
      values = {col: caget(pv) for pv, col in PV_MAP.items()}
      with psycopg2.connect(**db_config) as conn:
        with conn.cursor() as cur:
          sql = """
            INSERT INTO ess (timestamp, {columns})
            VALUES (%s, {placeholders})
            """.format(
              columns=", ".join(values.keys()),
              placeholders=", ".join(["%s"] * len(values))
            )
          cur.execute(sql, [timestamp] + list(values.values()))
          conn.commit()
      logger.debug("Logged values at %s", timestamp.isoformat())
    except Exception as e:
      logger.error("Error during logging: %s", e)
    time.sleep(10)

if __name__ == '__main__':
  main()
