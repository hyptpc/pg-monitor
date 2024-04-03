#!/usr/bin/env python3

__author__ = 'Shuhei Hayakawa'

import datetime
import epics
import logging
import pandas as pd
import psycopg
import pytz
import subprocess
import threading
import time
import urllib

import pgpass

logger = logging.getLogger('__main__').getChild(__name__)

#______________________________________________________________________________
class ACC:
  def __init__(self, interval=10):
    self.will_stop = False
    self.interval = interval
    self.wait = True
    self.timeout = 1.0
    self.magnet_list = ['AK11D1', 'AK18D1', 'AH18', 'BSM1',
                        'K18Q1', 'K18Q2', 'K18D2', 'K18Q3',
                        'K18O1', 'K18Q4', 'K18S1',
                        'K18CM1', 'K18CM2', 'K18S2', 'K18Q5', 'K18Q6',
                        'K18D3', 'K18BRS3', 'K18BRQ7',
                        'K18BRD4', 'K18BRQ8', 'K18BRD5', 'DORA']

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
      for i, name in enumerate(self.magnet_list):
        cset = epics.caget(
          'HDPS:' + name + ':CSET', timeout=self.timeout)
        cmon = epics.caget(
          'HDPS:' + name + ':CMON', timeout=self.timeout)
        pol = epics.caget('HDPS:' + name + ':POL',
                          timeout=self.timeout, as_string=True)
        tap = (now, name, i, cset, cmon, pol)
        logger.debug(tap)
        insert_list.append(tap)
      sql = ('insert into magnet ' +
             '(timestamp, name, magnet_order, cset, cmon, pol) ' +
             'values(%s,%s,%s,%s,%s,%s)')
      cursor.executemany(sql, insert_list)
    except (psycopg.Error or psycopg.OperationalError) as e:
      if connection is not None:
        connection.rollback()
      logger.error(e)
      print(e)
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

a = ACC()

def start():
  a.start()

def stop():
  a.stop()

if __name__ == '__main__':
  from rich import print
  a = ACC()
  a.run()
