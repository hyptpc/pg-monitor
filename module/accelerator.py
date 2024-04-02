#!/usr/bin/env python3

__author__ = 'Shuhei Hayakawa'

import datetime
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

class ACC:
  def __init__(self, interval=10):
    self.will_stop = False
    self.url = 'http://www-cont.j-parc.jp/HD/index'
    self.interval = interval
    self.wait = True

  def __parse(self):
    try:
      return pd.read_html(self.url)
    except urllib.error.HTTPError as e:
      logger.error(e)
      return []

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
      data = self.__parse()
      if len(data) < 1:
        return
      data = data[0][1]
      connection = psycopg.connect(pgpass.pgpass)
      cursor = connection.cursor()
      insert_list = []
      now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
      run_number = data[1]
      shot_number = data[2]
      last_shot = '20' + data[3]
      mr_power = data[4].split()[0]
      mr_intensity = data[5].split()[0]
      mr_cycle = float(data[6].split()[0])*1e-3
      sx_duty = data[7].split()[0]
      sx_spill_length = data[8].split()[0]
      sx_extraction_efficiency = data[9].split()[0]
      hd_status = data[10]
      hd_mode = data[11]
      hd_mps_setting = data[12]
      hd_power_syim = data[13].split()[0]
      hd_intensity_syim = data[14].split()[0]
      hd_intensity_rgicm = data[15].split()[0]
      hd_b_intensity_bdmpim = data[16].split()[0]
      hd_b_intensity_bic = data[17].split()[0]
      insert_list.append((now,
                          run_number,
                          shot_number,
                          last_shot,
                          mr_power,
                          mr_intensity,
                          mr_cycle,
                          sx_duty,
                          sx_spill_length,
                          sx_extraction_efficiency,
                          hd_status,
                          hd_mode,
                          hd_mps_setting,
                          hd_power_syim,
                          hd_intensity_syim,
                          hd_intensity_rgicm,
                          hd_b_intensity_bdmpim,
                          hd_b_intensity_bic))
      sql = ('insert into accelerator ' +
             '(timestamp, run_number, shot_number, last_shot, ' +
             'mr_power, mr_intensity, mr_cycle, sx_duty, sx_spill_length, ' +
             'sx_extraction_efficiency, hd_status, hd_mode, ' +
             'hd_mps_setting, hd_power_syim, hd_intensity_syim, ' +
             'hd_intensity_rgicm, hd_b_intensity_bdmpim, hd_b_intensity_bic) '
             +'values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)')
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
  a = ACC()
  a.run()
