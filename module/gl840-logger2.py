from datetime import datetime
import json
import logging
import html.parser
import pytz
import psycopg2
import requests
import time

from myenv import db_config, get_logger

logger = get_logger('gl840')

ip_address = 'logger2.monitor.k18br'

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
    if '---' in data:
      data = '0'
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
    except Exception as e:
      logger.error(e)

  def run(self):
    while True:
      try:
        timestamp = datetime.now(pytz.timezone('Asia/Tokyo'))
        self.parse()
        logger.debug(self.get_data())
        logger.debug(datetime.now())
        with psycopg2.connect(**db_config) as conn:
          with conn.cursor() as cur:
            insert_list = []
            data = self.get_data()
            values = [self.ip_address]
            for key in data:
              channel = key
              channel_name = f'ch{key:02d}'
              value = data[key][0]
              unit = data[key][1]
              values.append(value)
              values.append(unit)
            sql = """
              INSERT INTO gl840 (timestamp, ip_address, {channels})
              VALUES (%s, {plaseholders})
              """.format(
                channels=', '.join([f'ch{str(i).zfill(2)}_value, ch{str(i).zfill(2)}_unit' for i in range(1, 21)]),
                plaseholders=', '.join(['%s'] * len(values))
              )
            logger.debug(f'{sql}, {values}')
            cur.execute(sql, [timestamp] + values)
      except Exception as e:
        logger.error(e)
      time.sleep(10)

#______________________________________________________________________________
if __name__ == '__main__':
  gl840 = GL840(ip_address)
  gl840.run()
