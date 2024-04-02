#!/usr/bin/env python3

__author__ = 'Shuhei Hayakawa'

'''
Recorder script for slow monitor system using PostgreSQL database
'''

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

logger = logging.getLogger('recorder')

top_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(top_dir, 'module'))

dbname = 'e73'
pgpass = f'host=localhost dbname={dbname} user=postgres password=pg'

rotators = dict()
tables = None

#______________________________________________________________________________
def __make_rotator(table_name):
  global rotators
  if table_name not in rotators:
    logger.debug(f'make rotator {table_name}')
    rotator = logging.getLogger(table_name)
    rotator.setLevel(logging.DEBUG)
    rotator.debug(f'make rotator {table_name}')
    file_name = os.path.join(top_dir, 'log', f'pg-{dbname}-{table_name}.csv.gz')
    handler = logging.handlers.RotatingFileHandler(file_name, backupCount=7)
    rotator.addHandler(handler)
    rotators[table_name] = (file_name, rotator, handler)

#______________________________________________________________________________
def __record_single(table_name):
  logger.info(f'start {table_name}')
  rotators[table_name][2].doRollover()
  with psycopg.connect(pgpass) as connection:
    with connection.cursor() as cursor:
      sql = f"COPY {table_name} TO stdout DELIMITER ',' CSV HEADER"
      # sql = f"COPY (SELECT * FROM {table_name} ORDER BY timestamp DESC LIMIT 100) TO stdout DELIMITER ',' CSV HEADER"
      logger.debug(sql)
      with cursor.copy(sql) as copy:
        with gzip.open(rotators[table_name][0], 'wb') as f:
          for data in copy:
            f.write(data)
  logger.info(f'recorded {table_name}')

#______________________________________________________________________________
def record():
  global tables
  try:
    log_conf = os.path.join(top_dir, 'logging_config.yml')
    with open(log_conf, 'r') as f:
      logging.config.dictConfig(yaml.safe_load(f))
    with psycopg.connect(pgpass) as connection:
      with connection.cursor() as cursor:
        sql = 'SELECT relname FROM pg_stat_user_tables'
        logger.debug(sql)
        cursor.execute(sql)
        tables = cursor.fetchall()
    for t in tables:
      if len(t) != 1:
        continue
      table_name = t[0]
      __make_rotator(table_name)
      t = threading.Thread(target=__record_single, args=(table_name,))
      t.daemon = True
      t.start()
  except KeyboardInterrupt:
    return
  thread_list = threading.enumerate()
  thread_list.remove(threading.main_thread())
  for t in thread_list:
    t.join()

#______________________________________________________________________________
def run(interval=60*60*24):
  base_time = time.time()
  next_time = 0
  while True:
    try:
      record()
      logger.info('waiting next record ...')
      next_time = ((base_time - time.time()) % interval) or interval
      time.sleep(next_time)
    except KeyboardInterrupt:
      return
  logger.info('bye')

#______________________________________________________________________________
if __name__ == '__main__':
  run()
  
