import os
import psycopg
import socket
import time

from myenv import db_config, get_logger

module_name = os.path.splitext(os.path.basename(__file__))[0]
logger = get_logger(module_name)

TERM = b'\r\n'

def drain(sock):
  ''' Discard stale replies left in the socket buffer. '''
  sock.setblocking(False)
  try:
    while sock.recv(1024):
      pass
  except (BlockingIOError, InterruptedError):
    pass
  finally:
    sock.settimeout(3.0)

def send(sock, command):
  ''' Send one command and return exactly one reply line. '''
  drain(sock)
  sock.sendall(command + TERM)
  buf = b''
  while TERM not in buf:
    chunk = sock.recv(1024)  # raises socket.timeout after 3 s
    if not chunk:
      raise ConnectionError('connection closed by device')
    buf += chunk
  return buf.split(TERM, 1)[0].decode().strip()

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
      conn = None
      timeouts = 0
      while True:
        try:
          f = float(send(sock, b'RDGFIELD?'))
          logger.debug(f'{f} {u}')
          if conn is None or conn.closed:
            conn = psycopg.connect(**db_config, autocommit=True)
            logger.info('db connected')
          conn.execute(
            'INSERT INTO field (name, field) VALUES (%s, %s)',
            ['d5', f])
        except KeyboardInterrupt:
          logger.warning('Ctrl-C detected')
          break
        except ConnectionError:
          raise  # exit so systemd (Restart=always) reconnects
        except socket.timeout:
          timeouts += 1
          logger.error(f'device timeout ({timeouts})')
          if timeouts >= 10:
            raise ConnectionError('device not responding')
        except psycopg.OperationalError as e:
          logger.error(f'db error: {e}')
          if conn is not None:
            conn.close()
          conn = None  # reconnect on next loop
        except Exception as e:
          logger.error(e)
        time.sleep(1)
  except Exception as e:
    logger.error(e)

if __name__ == '__main__':
  main()
