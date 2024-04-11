#!/usr/bin/env python3

import datetime
import logging
import os
import psycopg
import pytz
import re
import threading
import time

import pgpass

logger = logging.getLogger('__main__').getChild(__name__)

#______________________________________________________________________________
class HDDAQ:
  def __init__(self, interval=10):
    self.interval = interval
    # self.top_dir = '/misc/oper/e73_ctrl'
    self.top_dir = '/misc/data/e73_2024'
    self.recorder_log = os.path.join(self.top_dir, 'recorder.log')
    self.runno_txt = os.path.join(self.top_dir, 'misc/runno.txt')
    self.evnum_txt = os.path.join(self.top_dir, 'misc/evnum.txt')
    self.comment_txt = os.path.join(self.top_dir, 'misc/comment.txt')
    self.starttime_txt = os.path.join(self.top_dir, 'misc/starttime.txt')
    self.will_stop = False
    self.runno = None
    self.comment = None
    self.starttime = None

  def parse_recorder_log(self):
    with open(self.recorder_log, 'r') as f:
      for line in f.readlines():
        print(line.split())
      
  def __parse_event_number(self):
    with open(self.evnum_txt, 'r') as f:
      try:
        self.evnum = int(f.read())
      except ValueError:
        pass

  def __parse_run_number(self):
    with open(self.runno_txt, 'r') as f:
      try:
        self.runno = int(f.read())
      except ValueError:
        pass

  def __parse_comment(self):
    with open(self.comment_txt, 'r') as f:
      for line in f.readlines():
        p = r'RUN (.*)'
        runno = int(re.search(p, line).group(1)[:5])
        if runno != self.runno:
          continue
        p = r': (.*)'
        self.comment = re.search(p, line).group(1)

  def __parse_starttime(self):
    with open(self.starttime_txt, 'r') as f:
      self.starttime = f.read()

  def __insert(self):
    connection = None
    try:
      connection = psycopg.connect(pgpass.pgpass)
      cursor = connection.cursor()
      # now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
      tap = ('NOW()', self.runno, self.evnum, self.starttime, self.comment)
      cursor.execute("INSERT INTO hddaq (timestamp, run_number, event_number, start_time, comment) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (run_number) DO UPDATE SET timestamp=NOW()", tap)
      logger.debug(f'{tap}')
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

  def __updater(self):
    self.__parse_run_number()
    self.__parse_event_number()
    self.__parse_comment()
    self.__parse_starttime()
    self.__insert()

  def run(self):
    base_time = time.time()
    next_time = 0
    while not self.will_stop:
      try:
        t = threading.Thread(target=self.__updater)
        t.daemon = True
        t.start()
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

d = HDDAQ()

def start():
  d.start()

def stop():
  d.stop()

if __name__ == '__main__':
  d = HDDAQ()
  # d.run()
  d.parse_recorder_log()
