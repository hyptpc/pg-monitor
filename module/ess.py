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

logger = logging.getLogger('__main__').getChild(__name__)

class ESS:
  def __init__(self, interval=10):
    self.will_stop = False
    self.url = 'http://www-cont.j-parc.jp/HD/separator'
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
    alert = False
    try:
      connection = psycopg.connect(pgpass.pgpass)
      cursor = connection.cursor()
      insert_list = []
      now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
      for i in range(2):
        name = f'ESS{i+1}'
        pvhead = 'HDESS:K18_' + name + ':'
        for electrode in ['POS', 'NEG']:
          vset = epics.caget(pvhead+electrode+'_VSET',
                             timeout=self.timeout)
          vmon = epics.caget(pvhead+electrode+'_VMON',
                             timeout=self.timeout)
          imon = epics.caget(pvhead+electrode+'_IMON',
                             timeout=self.timeout)
          if imon is not None and imon > 50:
            alert = True
          tap = (name, now, electrode, vset, vmon, imon, None)
          insert_list.append(tap)
      for i in range(2):
        name = f'ESS{i+1}'
        pvname = 'HDESS:K18_' + name + ':CCG_PMON'
        vacuum = epics.caget(pvname, timeout=self.timeout)
        tap = (name, now, None, None, None, None, vacuum)
        insert_list.append(tap)
      sql = ('insert into ess ' +
             '(name, timestamp, electrode, vset, vmon, imon, vacuum) '
             +'values(%s,%s,%s,%s,%s,%s,%s)')
      cursor.executemany(sql, insert_list)
      if alert:
        logger.warning(f'detect alert {insert_list}')
        subprocess.run(['aplay', '/home/oper/pg-monitor/sound/alert_sound.wav'])
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

e = ESS()

def start():
  e.start()

def stop():
  e.stop()

if __name__ == '__main__':
  e = ESS()
  e.run()
