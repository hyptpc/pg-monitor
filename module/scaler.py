#!/usr/bin/env python3

import datetime
import logging
import os
import pandas
import psycopg
import pytz
import re
import threading
import time

import pgpass

logger = logging.getLogger('__main__').getChild(__name__)

#______________________________________________________________________________
def tail(file_name, n=1):
  if n == 1:
    is_list = False
  elif type(n) != int or n < 1:
    raise ValueError('n must be a positive integer')
  else:
    is_list = True
  chunk_size = 64 * n
  with open(file_name, 'rb') as f:
    f.readline()
    left_end = f.tell() - 1
    f.seek(-1, 2)
    while True:
      if f.read(1).strip() != b'':
        right_end = f.tell()
        break
      f.seek(-2, 1)
    unread = right_end - left_end
    num_lines = 0
    line = b''
    while True:
      if unread < chunk_size:
        chunk_size = f.tell() - left_end
      f.seek(-chunk_size, 1)
      chunk = f.read(chunk_size)
      line = chunk + line
      f.seek(-chunk_size, 1)
      unread -= chunk_size
      if b'\n' in chunk:
        num_lines += chunk.count(b'\n')
        if num_lines >= n or not unread:
          leftmost_blank = re.search(rb'\r?\n', line)
          line = line[leftmost_blank.end():]
          line = line.decode()
          lines = re.split(r'\r?\n', line)
          result = [list(map(int, line.split(' '))) for line in lines[-n:]]
          if not is_list:
            return result[-1]
          else:
            return result

#______________________________________________________________________________
class SCALER:
  def __init__(self, interval=0.5):
    self.interval = interval
    self.top_dir = '/misc/daqhar-home/oper/scaler/e73/data'
    self.scaler_all_txt = os.path.join(self.top_dir, 'scaler_all.txt')
    self.wait = False
    self.will_stop = False
    self.last_line = None

  def __updater(self):
    connection = None
    try:
      last_line = tail(self.scaler_all_txt)
      if last_line == self.last_line:
        return
      else:
        self.last_line = last_line
      connection = psycopg.connect(pgpass.pgpass)
      cursor = connection.cursor()
      value = str(last_line[2:]).replace('[', '{').replace(']', '}')
      timestamp = last_line[0]
      trigger = int(last_line[1])
      if trigger == 1:
        trigger = 'SpillOn'
      elif trigger == 10:
        trigger = 'SpillOff'
      elif trigger == 100:
        trigger = 'Clock'
      else:
        trigger = 'Unknown'
      tap = ('NOW()',
             # timestamp, 
             trigger, value)
      logger.debug(f'{tap}')
      cursor.execute("INSERT INTO scaler (timestamp, trigger, value) VALUES (%s, %s, %s)", tap)
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

d = SCALER()

def start():
  d.start()

def stop():
  d.stop()

if __name__ == '__main__':
  d = SCALER()
  d.run()
