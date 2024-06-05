#!/usr/bin/env python3

import datetime
import logging
import pytz
import psycopg
import random
import time
import threading

import pgpass
import pmx_a

logger = logging.getLogger('__main__').getChild(__name__)

class KIKUSUI:
  def __init__(self, ip_address, interval=10):
    self.ip_address = ip_address
    self.interval = interval
    self.will_stop = False
    self.wait = True

  def __updater(self):
    logger.debug(datetime.datetime.now())
    connection = None
    try:
      connection = psycopg.connect(pgpass.pgpass)
      cursor = connection.cursor()
      insert_list = []
      now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
      device = pmx_a.PMX_A(self.ip_address, timeout=3.0, debug=False)
      if not device.is_open:
        logger.warning(f'{self.__class__.__name__} cannot connect to {self.ip_address}')
        return
      idn = device.idn()
      channel = 0
      meas_volt = device.volt()
      meas_curr = device.curr()
      output = bool(device.outp())
      stat = device.stat()
      tap = (device.host, idn, channel, now, output, meas_volt, meas_curr)
      insert_list.append(tap)
      sql = ('insert into kikusui '+
             '(ip_address, idn, channel, timestamp, output, meas_volt, meas_curr) '+
             'values(%s,%s,%s,%s, %s, %s, %s)')
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

  def start(self):
    logger.debug('start')
    t = threading.Thread(target=self.run)
    t.daemon = True
    t.start()

  def stop(self):
    logger.debug('stop')
    self.will_stop = True

devices = [
  KIKUSUI('192.168.1.121'),
  KIKUSUI('192.168.1.122'),
  KIKUSUI('192.168.1.123'),
  KIKUSUI('192.168.1.124'),
  KIKUSUI('192.168.1.125'),
  KIKUSUI('192.168.1.126'),
]

def start():
  for d in devices:
    d.start()

def stop():
  for d in devices:
    d.stop()

if __name__ == '__main__':
  start()
