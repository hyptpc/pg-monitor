#!/usr/bin/env python3

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
      beam_t1_mean_x = epics.caget('HDRGPM:T1IN:MEAN_X',
                                   timeout=self.timeout)
      beam_t1_mean_y = epics.caget('HDRGPM:T1IN:MEAN_Y',
                                   timeout=self.timeout)
      beam_t1_sigma_x = epics.caget('HDRGPM:T1IN:SIGMA_X',
                                    timeout=self.timeout)
      beam_t1_sigma_y = epics.caget('HDRGPM:T1IN:SIGMA_Y',
                                    timeout=self.timeout)
      pps_k18_cntr1_1s = epics.caget('HDPPS:K18:CNTR1_1S',
                                     timeout=self.timeout)
      pps_k18_cntr1_intg_hr = epics.caget(
        'HDPPS:K18:CNTR1_INTG_HR', timeout=self.timeout)
      pps_k18br_cntr1_1s = epics.caget(
        'HDPPS:K18BR:CNTR1_1S', timeout=self.timeout)
      pps_k18br_cntr1_intg_hr = epics.caget(
        'HDPPS:K18BR:CNTR1_INTG_HR', timeout=self.timeout)
      rad_org0201g = epics.caget(
        'RADHD:ORG0201G:VAL:LEVEL', timeout=self.timeout)
      rad_org0201n = epics.caget(
        'RADHD:ORG0201N:VAL:LEVEL', timeout=self.timeout)
      rad_org0202g = epics.caget(
        'RADHD:ORG0202G:VAL:LEVEL', timeout=self.timeout)
      rad_org0202n = epics.caget(
        'RADHD:ORG0202N:VAL:LEVEL', timeout=self.timeout)
      tap = (now,
             beam_t1_mean_x,
             beam_t1_mean_y,
             beam_t1_sigma_x,
             beam_t1_sigma_y,
             pps_k18_cntr1_1s,
             pps_k18_cntr1_intg_hr,
             pps_k18br_cntr1_1s,
             pps_k18br_cntr1_intg_hr,
             rad_org0201g,
             rad_org0201n,
             rad_org0202g,
             rad_org0202n)
      logger.debug(tap)
      insert_list.append(tap)
      sql = ('insert into beam ' +
             '(timestamp, beam_t1_mean_x, beam_t1_mean_y, beam_t1_sigma_x, ' +
             'beam_t1_sigma_y, pps_k18_cntr1_1s, pps_k18_cntr1_intg_hr, ' +
             'pps_k18br_cntr1_1s, pps_k18br_cntr1_intg_hr, ' +
             'rad_org0201g, rad_org0201n, rad_org0202g, rad_org0202n) '
             +'values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)')
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
