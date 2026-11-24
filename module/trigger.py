import psycopg2
import re
from datetime import datetime
import time

from myenv import db_config, get_logger

logger = get_logger('trigger')

last_log = '/home/oper/share/hul-trig-ctrl/last.log'
n_rgn2 = 6
INTERVAL = 5      # seconds between reads of last.log
HEARTBEAT = 3600  # write the unchanged setting at least this often (s)
beam_detectors = ['BH1-unused', 'BH2', 'BAC-unused', 'HTOF', 'T0', 'BH2-6']
scat_detectors = ['BEAM', 'SAC', 'KVC2', 'TOF-unused',
                  'KVC1', 'WC-unused', 'BHT', 'BAC',
                  'M3D-unused', 'HTOF-Mp2', 'HTOF-Mp3']

#______________________________________________________________________________
def bps(ctrl, coin):
  if ctrl == 0:
    return 'OFF'
  if coin == 0:
    return 'VETO'
  return 'ON'

#______________________________________________________________________________
def beam_bps(ctrl, coin):
  buf = ''
  for i, d in enumerate(beam_detectors):
    b = bps((ctrl>>(len(beam_detectors)-1-i))&1,
            (coin>>(len(beam_detectors)-1-i))&1)
    if 'OFF' in b:
      continue
    elif 'VETO' in b:
      buf += '/'
    buf += d + 'x'
  if buf[-1:] == 'x':
    buf = buf[:-1]
  return buf

#______________________________________________________________________________
def scat_bps(ctrl, coin, beam):
  buf = ''
  for i, d in enumerate(scat_detectors):
    b = bps((ctrl>>(len(scat_detectors)-1-i))&1,
            (coin>>(len(scat_detectors)-1-i))&1)
    if 'OFF' in b:
      continue
    elif 'VETO' in b:
      buf += '/'
    if i == 0:
      buf += beam + 'x'
    else:
      buf += d + 'x'
  if buf[-1:] == 'x':
    buf = buf[:-1]
  if len(buf) == 0:
    buf = ''
  return buf

#______________________________________________________________________________
def onoff(val, char=False):
  on = '!' if char else 'on'
  off = '.' if char else 'off'
  if val == 0:
    return f'{off}'
  elif val == 1:
    return f'{on}'
  else:
    return ''

#______________________________________________________________________________
def read_last_log():
  record = {}
  with open(last_log, 'r') as f:
    for line in f:
      if len(line.strip().split()) == 1:
        record['param_file'] = line.strip()
      if "::" in line:
        parts = line.strip().split()
        if len(parts) >= 2:
          key_raw, value = parts[0], parts[1]
          key = key_raw.lower().replace('::', '_')
          # key = re.sub(r'[^a-zA-Z0-9]', '_', key_raw).lower().replace('__', '_')
          try:
            record[key] = int(value)
          except ValueError:
            pass

  sel_psor = record['rgn3_sel_psor']
  # abc = chr(65+i)
  for i in range(n_rgn2):
    abc = chr(97+i)
    sel = onoff((sel_psor >> i) & 1)
    ps = record[f'rgn3_ps_r2{abc}'] + 1
    ctrl = record[f'rgn2{abc}_bps_ctrl_beam']
    coin = record[f'rgn2{abc}_bps_coin_beam']
    beam = beam_bps(ctrl, coin)
    ctrl = record[f'rgn2{abc}_bps_ctrl_scat']
    coin = record[f'rgn2{abc}_bps_coin_scat']
    scat = scat_bps(ctrl, coin, beam)
    record[f'trig_{abc.lower()}'] = scat
    
  return record

#______________________________________________________________________________
def insert(conn, record):
  record = dict(record, timestamp=datetime.now().astimezone())
  columns = ', '.join(record.keys())
  placeholders = ', '.join(['%s'] * len(record))
  with conn.cursor() as cur:
    cur.execute(f'INSERT INTO trigger ({columns}) VALUES ({placeholders})',
                list(record.values()))

#______________________________________________________________________________
def main():
  logger.info('start')
  conn = None
  last_record = None
  last_insert = 0.
  while True:
    try:
      record = read_last_log()
      changed = record != last_record
      if changed or time.time() - last_insert >= HEARTBEAT:
        if conn is None or conn.closed:
          conn = psycopg2.connect(**db_config)
          conn.autocommit = True
        insert(conn, record)
        if changed and last_record is not None:
          logger.info(f'trigger setting changed: {record.get("param_file")}')
        last_record = record
        last_insert = time.time()
    except psycopg2.Error as e:
      logger.error(e)
      if conn is not None:
        conn.close()
      conn = None
    except Exception as e:
      logger.error(e)
    time.sleep(INTERVAL)

if __name__ == '__main__':
  main()
