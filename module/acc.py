import time
from datetime import datetime, timezone
from epics import caget
import psycopg2
import logging

from myenv import db_config, get_logger

module_name = os.path.splitext(os.path.basename(__file__))[0]
logger = get_logger(module_name)

pv_map = {
  'HDSYS:RUN_NO': 'run_no',
  'HDSYS:SHOT_NO': 'shot_no',
  'HDSYS:MR_CYCLE': 'mr_cycle',
  # 'HDSYS:MR_POWER': 'mr_power',
  'MRMON:DCCT_073_1:VAL:MRPWR': 'mr_power',
  'HDSYS:OPR:MODE': 'opr_mode',
  'HDMON:MR_P3:INTENSITY': 'mr_p3_intensity',
  'HDMON:SYIM:POWER': 'syim_power',
  'HDMON:SYIM:INTENSITY': 'syim_intensity',
  'HDMON:BDMPIM:INTENSITY': 'bdmpim_intensity',
  'MRSLW:SXOPR_D2:VAL:DUTY': 'sx_duty',
  'MRSLW:SXOPR_D2:VAL:ExtEffi': 'sx_ext_effi',
  'MRSLW:SXOPR_D2:VAL:SpLen': 'sx_splen',
  'HDRGPM:T1IN:MEAN_X': 't1_mean_x',
  'HDRGPM:T1IN:MEAN_Y': 't1_mean_y',
  'HDRGPM:T1IN:SIGMA_X': 't1_sigma_x',
  'HDRGPM:T1IN:SIGMA_Y': 't1_sigma_y',
}

#_________________________________
def main():
  while True:
    try:
      timestamp = datetime.now(timezone.utc)
      values = {
        # col: caget(pv)
        col: caget(pv, as_string=True) if col in ['opr_mode'] else caget(pv)
        for pv, col in pv_map.items()
      }
      # logger.info(f'{values}')
      with psycopg2.connect(**db_config) as conn:
        with conn.cursor() as cur:
          sql = """
            INSERT INTO acc (timestamp, {columns})
            VALUES (%s, {placeholders})
            """.format(
              columns=", ".join(values.keys()),
              placeholders=", ".join(["%s"] * len(values))
            )
          cur.execute(sql, [timestamp] + list(values.values()))
          conn.commit()
      logger.debug("Logged values at %s", timestamp.isoformat())
    except Exception as e:
      logger.error(e)
    time.sleep(4)

if __name__ == '__main__':
  main()
