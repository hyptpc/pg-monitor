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
    with socket.create_connection(('192.168.20.18', 4196)) as sock:
      sock.settimeout(3.0)
      logger.info('connected')
      idn = send(sock, b'*IDN?')
      logger.info(idn)
      a = send(sock, b'auto?')
      r = send(sock, b'range?')
      logger.info(f'auto={a} range={r}')
      while True:
        try:
          f = send(sock, b'field?')
          m = send(sock, b'fieldm?')
          if m == 'm': m = 1.e-3
          elif m == '': m = 1.
          elif m == 'k': m = 1.e3
          f = float(f) * m
          u = send(sock, b'unit?')
          r = send(sock, b'range?')
          logger.debug(f'{f:.3f} {u}')
          with psycopg.connect(**db_config) as conn:
            with conn.cursor() as cur:
              sql = """
              INSERT INTO field (
              name, field ) VALUES ( %s, %s )
              """
              cur.execute(sql, ['shs2', f])
        except KeyboardInterrupt:
          print('Ctrl-C detected')
          break
        except Exception as e:
          print(e)
        time.sleep(0.5)
  except Exception as e:
    print(e)

if __name__ == '__main__':
  main()
