import csv
import os
import psycopg2
from datetime import datetime, timedelta
import time

from myenv import db_config, get_logger

logger = get_logger('shs')

data_dir = '/misc/shsdata/Trend/1sec/TrendOutputGroup1/'

def run():
  cutoff = datetime.now() - timedelta(minutes=5)
  # cutoff = datetime.now() - timedelta(days=3)
  with psycopg2.connect(**db_config) as conn:
    with conn.cursor() as cur:
      for fname in sorted(os.listdir(data_dir)):
        if fname.endswith(".csv"):
          fpath = os.path.join(data_dir, fname)
          mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
          if mtime < cutoff:
            continue
          with open(os.path.join(data_dir, fname)) as f:
            reader = csv.DictReader(f)
            for row in reader:
              dt = datetime.strptime(row["Date Time"], "%Y/%m/%d %H:%M:%S")
              values = [dt] + [float(row[col]) for col in reader.fieldnames[1:]]
              placeholders = ','.join(['%s'] * len(values))
              columns = ['timestamp'] + [col.lower().replace('fc0.', '').replace('.', '_') for col in reader.fieldnames[1:]]
              sql = f"""
                  INSERT INTO shs ({','.join(columns)})
                  VALUES ({placeholders})
                  ON CONFLICT (timestamp) DO NOTHING
              """
              # sql = f"""
              #     INSERT INTO shs ({','.join(columns)})
              #     VALUES ({placeholders})
              #     ON CONFLICT (timestamp) DO UPDATE SET
              #     {', '.join(f"{col}=EXCLUDED.{col}" for col in columns[1:])}
              # """
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
