import os
import psycopg
import socket
import serial
import time

from myenv import db_config, get_logger

module_name = os.path.splitext(os.path.basename(__file__))[0]
logger = get_logger(module_name)

TERM = b'\r\n'

def send(sock, command):
  sock.send(command + TERM)
  time.sleep(0.1)
  data = sock.recv(1024)
  return data.decode().strip()

def main():
  try:
    with socket.create_connection(('192.168.20.19', 4196)) as sock:
      sock.settimeout(3.0)
      logger.info('connected')
      idn = send(sock, b'*IDN?')
      u = send(sock, b'UNIT?')
      a = send(sock, b'AUTO?')
      r = send(sock, b'RANGE?')
      logger.info(f'idn={idn}, unit={u}, auto={a}, range={r}')
      while True:
        try:
          f = float(send(sock, b'RDGFIELD?'))
          logger.debug(f'{f} {u}')
          with psycopg.connect(**db_config) as conn:
            with conn.cursor() as cur:
              sql = """
              INSERT INTO field (
              name, field ) VALUES ( %s, %s )
              """
              cur.execute(sql, ['d5', f])
        except KeyboardInterrupt:
          print('Ctrl-C detected')
          break
        except Exception as e:
          print(e)
        # time.sleep(0.1)
  except Exception as e:
    print(e)

if __name__ == '__main__':
  main()
