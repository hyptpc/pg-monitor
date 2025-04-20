import logging
import os
import gzip
import psycopg2
from datetime import datetime, timedelta

from myenv import db_config, get_logger

logger = get_logger('daily-recorder')

BACKUP_BASE_DIR = '/home/oper/share/pg-monitor/csv'
TABLES = ['dhcp', 'ess', 'gl840']

if __name__ == '__main__':
  conn = psycopg2.connect(**db_config)
  conn.autocommit = True
  cur = conn.cursor()

  for table in TABLES:
    logger.info(f'▶ Processing table: {table}')
    output_dir = os.path.join(BACKUP_BASE_DIR, table)
    os.makedirs(output_dir, exist_ok=True)
    cur.execute(f'SELECT min(timestamp), max(timestamp) FROM {table}')
    min_ts, max_ts = cur.fetchone()
    if not min_ts or not max_ts:
      logger.info(f'  ⚠ No data in table: {table}. Skipping.')
      continue
    current_date = min_ts.date()
    end_date = max_ts.date()
    while current_date <= end_date:
      fname = f'{table}_{current_date}.csv.gz'
      filepath = os.path.join(output_dir, fname)
      if os.path.exists(filepath):
        logger.info(f'  Skipping {current_date} (already exists)')
      else:
        logger.info(f'  Exporting {current_date} → {fname}')
        start_dt = datetime.combine(current_date, datetime.min.time())
        end_dt = start_dt + timedelta(days=1)
        sql = f"""
          COPY (
            SELECT * FROM {table}
            WHERE timestamp >= TIMESTAMPTZ '{start_dt.isoformat()}'
            AND timestamp < TIMESTAMPTZ '{end_dt.isoformat()}'
          ) TO STDOUT WITH CSV HEADER
        """
        try:
          with open(filepath, 'wb') as f_out:
            with gzip.GzipFile(fileobj=f_out, mode='wb') as gz_out:
              cur.copy_expert(sql, gz_out)
        except Exception as e:
          logger.error(f'  ❌ Failed to export {current_date}: {e}')
          if os.path.exists(filepath):
            os.remove(filepath)
      current_date += timedelta(days=1)
  cur.close()
  conn.close()
