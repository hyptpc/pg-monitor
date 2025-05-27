import csv
import os
import math
import psycopg2
import socket
from datetime import datetime, timezone
import time

from myenv import db_config, get_logger

module_name = os.path.splitext(os.path.basename(__file__))[0]
logger = get_logger(module_name)

def query(command):
  host = 'omniace'
  port = 2300
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(2.0)
    s.connect((host, port))
    s.sendall((command+'\r\n').encode())
    response = s.recv(4096)
    data = response.decode().strip()
    data = [float(x) if x != '?' else math.nan for x in data.split(',')]
    logger.debug(data)
    return data

def run():
  with psycopg2.connect(**db_config) as conn:
    with conn.cursor() as cur:
      timestamp = datetime.now(timezone.utc)
      values = query('IDA A')
      placeholders = ','.join(['%s'] * (1 + len(values)))
      columns = ['timestamp'] + [f'ch{str(i+1).zfill(2)}' for i in range(18)]
      logger.debug(columns)
      sql = f"""
      INSERT INTO omniace ({','.join(columns)})
      VALUES ({placeholders})
      """
      logger.debug(sql)
      cur.execute(sql, [timestamp] + values)
      conn.commit()

def main():
  while True:
    try:
      run()
    except Exception as e:
      logger.error(e)
    time.sleep(20)

if __name__ == '__main__':
  main()
