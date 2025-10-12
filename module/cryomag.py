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

host = '192.168.20.24'
port = 4444

def parse_float(response):
  return float(''.join(
    c for c in response
    if (c.isdigit() or c == '.' or c == '-' )))

def query(command):
  try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
      s.settimeout(2.0)
      s.connect((host, port))
      s.sendall((command+'\r\n').encode())
      response = s.recv(4096)
      data = response.decode().strip()
      logger.debug(data)
      return data
  except socket.timeout:
    return 'timeout'

def run():
  with psycopg2.connect(**db_config) as conn:
    with conn.cursor() as cur:
      timestamp = datetime.now(timezone.utc)
      idn = query('*IDN?')
      logger.debug(idn)
      if idn == 'timeout':
        iout = 0
        vout = 0
        imag = 0
        vmag = 0
        sweep = 'off'
        mode = 'off'
        pshtr = False
      else:
        iout = parse_float(query('IOUT?'))
        vout = parse_float(query('VOUT?'))
        imag = parse_float(query('IMAG?'))
        vmag = parse_float(query('VMAG?'))
        sweep = query('SWEEP?')
        mode = query('MODE?')
        pshtr = query('PSHTR?') == '1'
      values = (timestamp, iout, vout, imag, vmag, sweep, mode, pshtr)
      placeholders = ','.join(['%s'] * len(values))
      columns = ['timestamp', 'iout', 'vout', 'imag', 'vmag', 'sweep', 'mode', 'ps_heater']
      sql = f"""
      INSERT INTO cryomag ({','.join(columns)})
      VALUES ({placeholders})
      """
      logger.debug(sql)
      cur.execute(sql, values)
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
