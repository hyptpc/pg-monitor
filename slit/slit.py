#!/usr/bin/env python3

import csv
import datetime
import logging
import os
import psycopg
import pytz
import rich.logging
import sys
import threading
import time

import keithley
import pgpass

pgpass.host = '192.168.1.157'

logger = logging.getLogger('__main__')

#______________________________________________________________________________
class SLIT:
  def __init__(self, port="/dev/ttyUSB0", interval=10):
    self.port = port
    self.interval = interval
    self.wait = True
    self.will_stop = False
    self.device = keithley.Keithley(port=self.port)
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

  def run(self):
    base_time = time.time()
    next_time = 0
    while not self.will_stop:
      try:
        t = threading.Thread(target=self.__updater)
        t.daemon = True
        t.start()
        if self.wait:
          t.join()
        next_time = ((base_time - time.time()) % self.interval) or self.interval
        time.sleep(next_time)
      except KeyboardInterrupt:
        break

  def __updater(self):
    logger.debug(datetime.datetime.now())
    connection = None
    try:
      connection = psycopg.connect(pgpass.eval())
      cursor = connection.cursor()
      insert_list = []
      now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
      ret = self.device.scan()
      ret = ret.replace(r"b", '').replace(r"'", '')
      raw_values = []
      cor_values = []
      for row in csv.reader(ret.strip().splitlines()):
        for column in row:
          raw_values.append(float(column))
      for i in range(len(self.calib_params)):
        c = raw_values[i] * self.calib_params[i][0] + self.calib_params[i][1]
        cor_values.append(c)
      tap = (now,
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
      insert_list.append(tap)
      sql = ('insert into slit ' +
             '(timestamp, ' +
             'ifh_minus_raw, ifh_plus_raw, ifv_minus_raw, ifv_plus_raw, ' +
             'mom_minus_raw, mom_plus_raw, mass1_minus_raw, mass1_plus_raw, ' +
             'ifh_minus_cor, ifh_plus_cor, ifv_minus_cor, ifv_plus_cor, ' +
             'mom_minus_cor, mom_plus_cor, mass1_minus_cor, mass1_plus_cor) ' +
             'values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)')
      cursor.executemany(sql, insert_list)
      logger.info(f'success query: {tap}')
    except (psycopg.Error or psycopg.OperationalError) as e:
      if connection is not None:
        connection.rollback()
      logger.error(e)
      print(e)
      return
    except KeyboardInterrupt:
      self.will_stop = True
      return
    connection.commit()
    cursor.close()
    connection.close()

  def start(self):
    logger.debug('start')
    t = threading.Thread(target=self.run)
    t.daemon = True
    t.start()
    t.join()

  def stop(self):
    logger.debug('stop')
    self.will_stop = True

devices = [SLIT(port="/dev/ttyUSB0")]

def start():
  for d in devices:
    d.start()

def stop():
  for d in devices:
    d.stop()

if __name__ == '__main__':
  logging.basicConfig(
    level=logging.INFO,
    format='%(name)s %(funcName)s : %(message)s',
    handlers=[rich.logging.RichHandler(rich_tracebacks=True)],
  )
  start()
