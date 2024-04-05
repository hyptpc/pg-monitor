#!/usr/bin/env python3

__author__ = 'Shuhei Hayakawa'

'''
Recorder script for slow monitor system using PostgreSQL database
'''

import datetime
import gzip
import logging
import logging.config
import os
import psycopg
import threading
import signal
import sys
import time
import yaml

top_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(top_dir, 'module'))

import pgpass

logger = logging.getLogger('recorder')

rotators = dict()
tables = None

#______________________________________________________________________________
def execute_sql(sql):
  try:
    with psycopg.connect(pgpass.pgpass) as connection:
      with connection.cursor() as cursor:
        logger.debug(sql)
        cursor.execute(sql)
        return cursor.fetchall()
  except psycopg.OperationalError as e:
    logger.error(e)

#______________________________________________________________________________
def __make_rotator(table_name):
  global rotators
  if table_name not in rotators:
    logger.debug(f'make rotator {table_name}')
    rotator = logging.getLogger(table_name)
    rotator.setLevel(logging.DEBUG)
    rotator.debug(f'make rotator {table_name}')
    file_name = os.path.join(top_dir, 'log',
                             f'pg-{pgpass.dbname}-{table_name}.csv.gz')
    handler = logging.handlers.RotatingFileHandler(file_name, backupCount=7)
    rotator.addHandler(handler)
    rotators[table_name] = (file_name, rotator, handler)

#______________________________________________________________________________
def __record_single(table_name, sql, file_name, doRollover=True):
  logger.info(f'start {table_name} ({file_name})')
  if doRollover:
    rotators[table_name][2].doRollover()
  try:
    with psycopg.connect(pgpass.pgpass) as connection:
      with connection.cursor() as cursor:
        logger.debug(sql)
        with cursor.copy(sql) as copy:
          with gzip.open(file_name, 'wb') as f:
            for data in copy:
              f.write(data)
  except psycopg.OperationalError as e:
    logger.error(e)
  logger.info(f'recorded {table_name} ({file_name})')

#______________________________________________________________________________
def __record_all():
  global tables
  try:
    tables = execute_sql('SELECT relname FROM pg_stat_user_tables')
    if tables is None:
      logger.error('table is None')
      return
    for t in tables:
      if len(t) != 1:
        continue
      table_name = t[0]
      __make_rotator(table_name)
      ''' all '''
      sql = f"COPY {table_name} TO stdout DELIMITER ',' CSV HEADER"
      file_name = rotators[table_name][0]
      t = threading.Thread(target=__record_single,
                           args=(table_name, sql, file_name))
      t.daemon = True
      t.start()
      ''' every day '''
      start = datetime.date(2024, 4, 1)
      end = datetime.date.today()
      for i in range((end - start).days):
        date = start + datetime.timedelta(i)
        daily_name = os.path.join(
          top_dir, 'log', 'daily',
          f'pg-{pgpass.dbname}-{table_name}-{str(date)}.csv.gz')
        if os.path.isfile(daily_name):
          continue
        sql = (f"SELECT COUNT(1) FROM {table_name} WHERE timestamp " +
               f"BETWEEN '{date}' AND '{date + datetime.timedelta(1)}'")
        count = execute_sql(sql)[0][0]
        if count == 0:
          continue
        sql = (f"COPY (SELECT * FROM {table_name} WHERE timestamp " +
               f"BETWEEN '{date}' AND '{date + datetime.timedelta(1)}') " +
               f"TO stdout DELIMITER ',' CSV HEADER")
        logger.debug(date)
        logger.debug(sql)
        logger.debug(daily_name)
        t = threading.Thread(target=__record_single,
                             args=(table_name, sql, daily_name, False))
        t.daemon = True
        t.start()
  except KeyboardInterrupt:
    return
  thread_list = threading.enumerate()
  thread_list.remove(threading.main_thread())
  for t in thread_list:
    t.join()

#______________________________________________________________________________
def __record_one_day():
  pass

#______________________________________________________________________________
def run(interval=60*60*24):
  if not os.path.exists(os.path.join(top_dir, 'log')):
    print('Plese prepare log directory.')
    return
  log_conf = os.path.join(top_dir, 'logging_config.yml')
  with open(log_conf, 'r') as f:
    logging.config.dictConfig(yaml.safe_load(f))
  base_time = time.time()
  next_time = 0
  while True:
    try:
      __record_all()
      logger.info('waiting next record ...')
      next_time = ((base_time - time.time()) % interval) or interval
      time.sleep(next_time)
    except KeyboardInterrupt:
      return
  logger.info('bye')

#______________________________________________________________________________
if __name__ == '__main__':
  run()

