from collections import defaultdict
from datetime import datetime
import logging
import os
import pytz
import psycopg2
import re
import time
import psycopg2

from myenv import db_config, get_logger

module_name = os.path.splitext(os.path.basename(__file__))[0]
logger = get_logger(module_name)

data_path = '/misc/data/e72'
comment_path = os.path.join(data_path, 'misc/comment.txt')
recorder_path = os.path.join(data_path, 'recorder.log')

#______________________________________________________________________________
def parse_comment_txt(path):
  runs = defaultdict(lambda: {
    'run_number': None,
    'start_time': None,
    'stop_time': None,
    'comment': None,
    'recorder': False,
    'event_number': None,
    'data_size_bytes': None
  })
  with open(path) as f:
    for line in f:
      m = re.match(r'(\d{4}) (\d{2})/(\d{2}) (\d{2}):(\d{2}):(\d{2}) \[RUN (\d+)\] (\w+)\s*:\s*(.*)',
                   line)
      if m:
        dt = datetime.strptime(f"{m[1]}-{m[2]}-{m[3]} {m[4]}:{m[5]}:{m[6]}", "%Y-%m-%d %H:%M:%S")
        run_number = int(m[7])
        keyword = m[8]
        comment = m[9].strip()

        r = runs[run_number]
        r['run_number'] = run_number
        if keyword == "START":
          r['start_time'] = dt
          r['comment'] = comment
        elif keyword.startswith("STOP"):
          r['stop_time'] = dt

  now = datetime.now()
  for r in runs.values():
    if r['start_time'] and not r['stop_time']:
      r['stop_time'] = None
  return runs

#______________________________________________________________________________
def parse_recorder_log(path, runs):
  with open(path) as f:
    for line in f:
      m = re.match(r'RUN\s+(\d+)\s*:\s+(.*?)\s*-\s*(.*?)\s*:\s+(\d+)\s+events\s*:\s+(\d+)\s+bytes',
                   line)
      if m:
        run_number = int(m[1])
        start = datetime.strptime(m[2], "%a %b %d %H:%M:%S %Y")
        stop = datetime.strptime(m[3], "%a %b %d %H:%M:%S %Y")
        events = int(m[4])
        size = int(m[5])
        r = runs.get(run_number, {})
        r.update({
          'run_number': run_number,
          'start_time': r.get('start_time') or start,
          'stop_time': r.get('stop_time') or stop,
          'event_number': events,
          'data_size_bytes': size,
          'recorder': True
        })
        runs[run_number] = r

#______________________________________________________________________________
def upsert_to_postgresql(runs):
  conn = psycopg2.connect(**db_config)
  cur = conn.cursor()
  for r in sorted(runs.values(), key=lambda x: x['run_number']):
  # for r in runs.values():
    # logger.info(r)
    cur.execute("""
      INSERT INTO hddaq (
        run_number, start_time, stop_time, comment,
        recorder, event_number, data_size_bytes
      )
      VALUES (%s, %s, %s, %s, %s, %s, %s)
      ON CONFLICT (run_number) DO UPDATE SET
        start_time = EXCLUDED.start_time,
        stop_time = EXCLUDED.stop_time,
        comment = EXCLUDED.comment,
        recorder = EXCLUDED.recorder,
        event_number = EXCLUDED.event_number,
        data_size_bytes = EXCLUDED.data_size_bytes;
    """, (
      r['run_number'],
      r['start_time'],
      r['stop_time'],
      r['comment'],
      r['recorder'],
      r['event_number'],
      r['data_size_bytes']
    ))
  conn.commit()
  cur.close()
  conn.close()

#______________________________________________________________________________
def main():
  logger.info('start')
  while True:
    try:
      runs = parse_comment_txt(comment_path)
      parse_recorder_log(recorder_path, runs)
      upsert_to_postgresql(runs)
    except Exception as e:
      logger.error(e)
    time.sleep(10)

#______________________________________________________________________________
if __name__ == '__main__':
  main()
  
