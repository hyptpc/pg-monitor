#!/usr/bin/env python3

import datetime
import json
import logging
import html.parser
import pytz
import psycopg
import requests
import threading
import time

logger = logging.getLogger('__main__').getChild(__name__)

#______________________________________________________________________________
class GL840(html.parser.HTMLParser):
  data_dict = dict()
  ch = None
  val = None
  unit = None

  #____________________________________________________________________________
  def __init__(self, ip_address='localhost', interval=10):
    super().__init__()
    self.ip_address = ip_address
    self.interval = interval
    self.wait = True
    self.will_stop = False

  #____________________________________________________________________________
  def handle_data(self, data):
    data = data.strip().replace(' ', '').replace('+', '')
    if len(data) == 0:
      return
    try:
      float(data)
    except ValueError:
      if 'CH' in data:
        self.ch = int(data[2:])
        self.val = None
        self.unit = None
      else:
        self.unit = data
    else:
      self.val = float(data)
    if (self.ch is not None and
        self.val is not None and
        self.unit is not None):
      self.data_dict[self.ch] = (self.val, self.unit)

  #____________________________________________________________________________
  def get_data(self, ch=None):
    if ch in self.data_dict:
      return self.data_dict[ch]
    else:
      return self.data_dict

  #____________________________________________________________________________
  def parse(self):
    try:
      ret = requests.get(f'http://{self.ip_address}/digital.cgi?chg=0')
      self.feed(ret.text)
    except:
      pass

  def __updater(self):
    self.parse()
    logger.debug(datetime.datetime.now())
    try:
      insert_list = []
      data = self.get_data()
      for key in data:
        now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
        channel = key
        channel_name = f'ch{key:02d}'
        value = data[key][0]
        unit = data[key][1]
        tap = (self.ip_address, now, channel, channel_name, value, unit)
        insert_list.append(tap)
      sql = 'insert into gl840 (ip_address, timestamp, channel, channel_name, value, unit) values(%s,%s,%s,%s,%s,%s)'
      self.cursor.executemany(sql, insert_list)
    except psycopg.Error as e:
      self.connection.rollback()
      logger.error(e.diag.message_primary)
      return
    except KeyboardInterrupt:
      return
    self.connection.commit()

  def run(self):
    self.connection = psycopg.connect('host=localhost dbname=e73 user=postgres password=pg')
    self.cursor = self.connection.cursor()
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
    self.cursor.close()
    self.connection.close()

  def start(self):
    logger.debug('start')
    t = threading.Thread(target=self.run)
    t.daemon = True
    t.start()

  def stop(self):
    logger.debug('stop')
    self.will_stop = True

g = GL840('192.168.1.113')

def start():
  g.start()

def stop():
  g.stop()

#______________________________________________________________________________
if __name__ == '__main__':
  gl840 = GL840('192.168.1.113')
  gl840.parse()
  gl840.run()
