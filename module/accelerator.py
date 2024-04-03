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
    self.url = 'http://www-cont.j-parc.jp/HD/index'
    self.interval = interval
    self.wait = True

  def __parse(self):
    ''' this method is obsolete '''
    return
    # try:
    #   return pd.read_html(self.url)
    # except urllib.error.HTTPError as e:
    #   logger.error(e)
    #   return []

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
      timeout = 1.0
      run_number = epics.caget('HDSYS:RUN_NO', timeout=timeout)
      shot_number = epics.caget('HDSYS:SHOT_NO', timeout=timeout)
      mr_power = epics.caget('MRMON:DCCT_073_1:VAL:MRPWR', timeout=timeout)
      mr_intensity = epics.caget('HDMON:MR_P3:INTENSITY', timeout=timeout)
      mr_cycle = epics.caget('HDSYS:MR_CYCLE', timeout=timeout)
      sx_duty = epics.caget('MRSLW:SXOPR_D2:VAL:DUTY', timeout=timeout)
      sx_spill_length = epics.caget('MRSLW:SXOPR_D2:VAL:SpLen', timeout=timeout)
      sx_extraction_efficiency = epics.caget('MRSLW:SXOPR_D2:VAL:ExtEffi', timeout=timeout)
      hd_mode = epics.caget('HDSYS:OPR:MODE', timeout=timeout, as_string=True)
      hd_power_syim = epics.caget('HDMON:SYIM:POWER', timeout=timeout)
      hd_intensity_syim = epics.caget('HDMON:SYIM:INTENSITY', timeout=timeout)
      hd_intensity_rgicm = epics.caget('HDMON:BDMPIM:INTENSITY', timeout=timeout)
      tap = (now, run_number, shot_number,
             mr_power, mr_intensity, mr_cycle,
             sx_duty, sx_spill_length, sx_extraction_efficiency,
             hd_mode, hd_power_syim, hd_intensity_syim,
             hd_intensity_rgicm)
      logger.debug(tap)
      insert_list.append(tap)
      sql = ('insert into accelerator ' +
             '(timestamp, run_number, shot_number, ' +
             'mr_power, mr_intensity, mr_cycle, sx_duty, sx_spill_length, ' +
             'sx_extraction_efficiency, hd_mode, ' +
             'hd_power_syim, hd_intensity_syim, ' +
             'hd_intensity_rgicm) '
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
