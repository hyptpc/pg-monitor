import csv
from datetime import datetime, timezone
import logging
import os
import psycopg2
import pytz
import sys
import threading
import time

import keithley

from myenv import db_config, get_logger

db_config['host'] = 'urazato'

logger = get_logger('slit')

#______________________________________________________________________________
class SLIT:
  def __init__(self, port="/dev/ttyUSB0", interval=10):
    self.port = port
    self.interval = interval
    self.wait = True
    self.will_stop = False
    self.device = keithley.Keithley(port=self.port)
    logger.debug(self.device.idn())
    self.device.setup_scan()
    self.calib_params = [
      (34.647, -145.5), # ifh-
      (35.103, -28.278), # ifh+
      (10.413, -15.835), # ifv+
      (9.9703, -35.024), # ifv-
      (36.000, -180.000), 
      (36.000, -180.000),
      (3.000, -15.000),
      (3.000, -15.000),
    ]

def main():
  device = SLIT(port="/dev/ttyUSB0")
  while True:
    try:
      timestamp = datetime.now(timezone.utc)
      ret = device.device.scan()
      ret = ret.replace(r"b", '').replace(r"'", '')
      logger.debug(ret)
      raw_values = []
      cor_values = []
      for row in csv.reader(ret.strip().splitlines()):
        for column in row:
          raw_values.append(float(column))
      if len(raw_values) >= 8:
        for i in range(len(device.calib_params)):
          c = raw_values[i] * device.calib_params[i][0] + device.calib_params[i][1]
          cor_values.append(c)
        tap = (timestamp,
               raw_values[0], raw_values[1],
               raw_values[3], raw_values[2],
               raw_values[4], raw_values[5],
               raw_values[7], raw_values[6],
               cor_values[0], cor_values[1],
               cor_values[3], cor_values[2],
               cor_values[4], cor_values[5],
               cor_values[7], cor_values[6],
        )
        logger.debug(tap)
        # insert_list.append(tap)
        sql = ('INSERT INTO slit ' +
               '(timestamp, ' +
               'ifh_minus_raw, ifh_plus_raw, ifv_minus_raw, ifv_plus_raw, ' +
               'mom_minus_raw, mom_plus_raw, ' +
               'mass1_minus_raw, mass1_plus_raw, ' +
               'ifh_minus_cor, ifh_plus_cor, ifv_minus_cor, ifv_plus_cor, ' +
               'mom_minus_cor, mom_plus_cor, ' +
               'mass1_minus_cor, mass1_plus_cor) ' +
               'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)')
        with psycopg2.connect(**db_config) as conn:
          with conn.cursor() as cur:
            cur.execute(sql, tap)
            conn.commit()
            logger.debug(f'success query: {tap}')
    except Exception as e:
      logger.error(e)
    time.sleep(20)

if __name__ == '__main__':
  main()
