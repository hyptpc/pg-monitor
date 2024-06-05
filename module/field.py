#!/usr/bin/env python3

import datetime
import epics
import logging
import psycopg
import pytz
import subprocess
import threading
import time

import pgpass
import lakeshore421
import lakeshore475

logger = logging.getLogger('__main__').getChild(__name__)

#______________________________________________________________________________
class FIELD:
  def __init__(self, name, cls, port, interval=10):
    self.will_stop = False
    self.interval = interval
    self.wait = True
    self.timeout = 1.0
    self.name = name
    self.port = port
    self.cls = cls

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
      connection = psycopg.connect(pgpass.pgpass)
      cursor = connection.cursor()
      insert_list = []
      now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
      device = self.cls(port=self.port)
      if device.serial is not None:
        idn = device.idn()
        logger.debug(idn)
        if 'MODEL475' in idn:
          device.ask('UNIT 2')
        val = device.read()
        # unit = device.unit()
        order = 22 if self.name == 'DORA' else 21 if self.name == 'K18BRD5' else 0
        tap = (now, self.name, order, val)
        logger.debug(tap)
        insert_list.append(tap)
      sql = ('insert into magnet ' +
             '(timestamp, name, magnet_order, field) ' +
             'values(%s,%s,%s,%s)')
      cursor.executemany(sql, insert_list)
    except (psycopg.Error or psycopg.OperationalError) as e:
      if connection is not None:
        connection.rollback()
      logger.error(e)
      return
    except KeyboardInterrupt:
      return
    connection.commit()
    cursor.close()
    connection.close()

  def start(self):
    logger.debug('start')
    t = threading.Thread(target=self.run)
    t.daemon = True
    t.start()

  def stop(self):
    logger.debug('stop')
    self.will_stop = True

devices = [FIELD('DORA', lakeshore421.Lakeshore421, '/dev/ttyADV1'),
           FIELD('K18BRD5', lakeshore475.Lakeshore475, '/dev/ttyADV0'),
           ]

def start():
  for d in devices:
    d.start()

def stop():
  for d in devices:
    d.stop()

if __name__ == '__main__':
  from rich import print
  start()
