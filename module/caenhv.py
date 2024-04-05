#!/usr/bin/env python3

import argparse
import datetime
import logging
import os
import pytz
import psycopg
import random
import subprocess
import sys
import time
import threading

import pgpass

logger = logging.getLogger('__main__').getChild(__name__)

tablename = 'caenhv'
read_caenhv = '/home/oper/monitor-tools/CAENHV/read-caenhv/bin/read-caenhv'

class CAENHV:
  def __init__(self, ip_address, crate_type, interval=10):
    self.interval = interval
    self.ip_address = ip_address
    self.crate_type = crate_type
    self.will_stop = False
    
  def __get_caen_data(self):
    ret = subprocess.run(
      [read_caenhv, '--host', self.ip_address,
       '--type', self.crate_type, '--action', 'cratemap'],
      capture_output=True, text=True)
    if ret.returncode != 0:
      logger.error(ret.stderr)
      return None
    data = dict()
    for line in ret.stdout.splitlines():
      columns = line.split()
      if len(columns) <= 1:
        continue
      if columns[0] == 'Board':
        board = int(columns[1])
        labels = None
        name = ' '.join(columns[2:])
        if name == 'Not Present':
          continue
        maxch = int(columns[3])
        data[board] = {'name': name, 'maxch': maxch}
      if columns[0] == 'BdStatus':
        data[board]['BdStatus'] = columns[1]
      if len(columns) == 10:
        if labels is None:
          labels = columns
        else:
          channel = int(columns[0])
          data[board][channel] = dict()
          for i in range(1, len(labels)):
            data[board][channel][labels[i]] = columns[i]
    return data

  def __updater(self):
    logger.debug(f'update {datetime.datetime.now()}')
    connection = None
    try:
      connection = psycopg.connect(pgpass.pgpass)
      cursor = connection.cursor()
      insert_list = []
      data = self.__get_caen_data()
      if data is None:
        return
      for key, value in data.items():
        now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
        board_slot = key
        board_name = value['name']
        board_status = value['BdStatus']
        maxch = value['maxch']
        for ch in range(maxch):
          channel_name = value[ch]['Name']
          v0set = float(value[ch]['V0Set'])
          i0set = float(value[ch]['V0Set'])
          vmon = float(value[ch]['VMon'])
          imon = float(value[ch]['VMon'])
          rup = float(value[ch]['RUp'])
          rdown = float(value[ch]['RDWn'])
          pw = value[ch]['Pw']
          channel_status = value[ch]['Status']
          tap = (self.ip_address, now, self.crate_type,
                 board_slot, board_name, board_status,
                 ch, channel_name, v0set, i0set, vmon, imon,
                 rup, rdown, pw, channel_status)
          insert_list.append(tap)
      sql = (f'insert into {tablename} ' +
             '(ip_address, timestamp, crate_type, board_slot, board_name, '
             +'board_status, channel, channel_name, v0set, i0set, vmon, imon, '
             +'rup, rdown, pw, channel_status) '
             +'values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)')
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

  def run(self, wait=True):
    base_time = time.time()
    next_time = 0
    while not self.will_stop:
      try:
        t = threading.Thread(target=self.__updater)
        t.daemon = True
        t.start()
        if wait:
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


caenhvs = [CAENHV(ip_address='192.168.1.171', crate_type='SY1527'),
           CAENHV(ip_address='192.168.1.172', crate_type='SY1527'),
           CAENHV(ip_address='192.168.1.173', crate_type='SY1527'),
           CAENHV(ip_address='192.168.1.174', crate_type='SY4527'),
           CAENHV(ip_address='192.168.1.175', crate_type='SY4527'),
           ]

def start():
  for c in caenhvs:
    c.start()

def stop():
  for c in caenhvs:
    c.stop()

if __name__ == '__main__':
  start()
