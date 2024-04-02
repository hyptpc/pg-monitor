#!/usr/bin/env python3

__author__ = 'Shuhei Hayakawa'

from pyModbusTCP.client import ModbusClient
import struct
import datetime
import logging
import psycopg
import pytz
import threading
import time

logger = logging.getLogger('__main__').getChild(__name__)

class Apiste():
  def __init__(self, ip_address='192.168.1.20', interval=10):
    self.interval = interval
    self.will_stop = False
    self.wait = True
    self.ip_address = ip_address
    self.client = ModbusClient(self.ip_address)
    self.open()
    logger.debug(f'open Apiste {self.ip_address}')
    logger.info(f'{self.log()}')
    logger.info(f'{self.status(0x1040)}')

  def open(self):
    self.client.open()

  def close(self):
    self.client.close()

  def on(self):
    self.client.write_single_register(0x2F00,1)

  def off(self):
    self.client.write_single_register(0x2F00,0)

  def is_running(self):
    val=self.client.read_holding_registers(0x2F00,2)
    return val[0]

  def read(self,reg=0x0000):
    val=self.client.read_holding_registers(reg,2)
    return val[0]*0.01

  def status(self,reg=0x2f00):
    val=self.client.read_holding_registers(reg,2)
    return val[0]

  def log(self):
    vals=[self.is_running(),self.read(0x0000),self.read(0x0002)]
    return vals

  def __updater(self):
    logger.debug(f'update {datetime.datetime.now()}')
    connection = None
    try:
      connection = psycopg.connect('host=localhost dbname=e73 user=postgres password=pg')
      cursor = connection.cursor()
      insert_list = []
      data = self.log()
      now = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
      tap = (self.ip_address, now, data[0], data[1], data[2])
      insert_list.append(tap)
      sql = (f'insert into apiste ' +
             '(ip_address, timestamp, status, tmon, tset) '
             +'values(%s,%s,%s,%s,%s)')
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
        if self.wait:
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

a = Apiste()

def start():
  a.start()

def stop():
  a.stop()

if __name__ == "__main__":
  a = Apiste()
  a.run()
  # a=Apiste()
  # dt = datetime.datetime.now()
  # fname=dt.strftime("apiste_%Y%m%d")
  # # f = open(fname + '.txt', 'a')
  # while True:
  #   dt = datetime.datetime.now()
  #   printout=dt.strftime("%Y%m%d_%H:%M:%S, ")
  #   printout+=str(int(time.mktime(dt.timetuple()))) + ", "
  #   printout+=','.join([ str(v) for v in a.log()])
  #   # f.write(printout+"\n")
  #   # f.flush()
  #   logger.error(printout)
  #   time.sleep(10)
  # # f.close()
