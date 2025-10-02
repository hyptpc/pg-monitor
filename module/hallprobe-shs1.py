import os
import pathlib
import psycopg
import serial
from datetime import datetime, timezone
import time

from myenv import db_config, get_logger

module_name = os.path.splitext(os.path.basename(__file__))[0]
logger = get_logger(module_name)

device = '/dev/ttyUSB0'
term = '\r\n'

db_config['host'] = 'urazato'

#_________________________________
def main():
  s = serial.Serial(device,
                    parity=serial.PARITY_ODD,
                    baudrate=57600,
                    timeout=0.5)
  logger.info('connected')
  while True:
    try:
      with psycopg.connect(**db_config) as conn:
        with conn.cursor() as cur:
          s.write(('rdgfield?' + term).encode('utf-8'))
          ret = s.read_until(b'\r\x8a')
          decoded = b''
          for d in ret:
            decoded += (d & 0x7f).to_bytes(1, 'big')
          field = float(decoded.decode())
          logger.debug(field)
          sql = """
          INSERT INTO field (
          name, field ) VALUES ( %s, %s )
          """
          cur.execute(sql, ['shs1', field])
    except Exception as e:
      logger.error(e)
    logger.debug('sleep')
    time.sleep(1)

if __name__ == '__main__':
  main()
