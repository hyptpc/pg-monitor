from caen_libs import caenhvwrapper as hv
import os
import psycopg
from datetime import datetime, timezone
import time
import sys

from myenv import db_config, get_logger

module_name = os.path.splitext(os.path.basename(__file__))[0]
logger = get_logger(module_name)

host = '192.168.20.52' # caenhv2
systype = 'SY5527'
linktype = 'TCPIP'

#______________________________________________________________________________
def main():
  logger.debug(f'CAEN HV Wrapper (version {hv.lib.sw_release()})')
  try:
    with hv.Device.open(hv.SystemType[systype], hv.LinkType[linktype],
                        host, 'admin', 'admin') as device:
        slots = device.get_crate_map()
        logger.info(f'crate map : {slots}')
        comm_list = device.get_exec_comm_list()
        logger.info(f'exec comm list {comm_list}')
        sys_props = device.get_sys_prop_list()
        logger.info(f'sys prop list {sys_props}')
        for prop_name in sys_props:
          prop_info = device.get_sys_prop_info(prop_name)
          if prop_info.mode is not hv.SysPropMode.WRONLY:
            try:
              prop_value = device.get_sys_prop(prop_name)
              if type(prop_value) == str:
                prop_value = prop_value.strip()
              logger.info(f'SYSPROP {prop_name}, {prop_info.type.name} {prop_value}')
              # device.subscribe_system_params([prop_name])
            except Exception as e:
              logger.error(f'SYSPROP {prop_name}, {prop_info.type.name} {e}')
        while True:
          now = datetime.now(timezone.utc)
          with psycopg.connect(**db_config) as conn:
            with conn.cursor() as cur:
              for board in slots:
                if board is None:
                  continue
                buf = f'{board}'
                bd_params = device.get_bd_param_info(board.slot)
                bd_values = dict()
                for param_name in bd_params:
                  param_prop = device.get_bd_param_prop(board.slot, param_name)
                  if param_prop.mode is not hv.ParamMode.WRONLY:
                    try:
                      param_value = device.get_bd_param([board.slot], param_name)
                      buf += f' {param_name}, {param_prop.type.name} {param_value[0]}'
                      # device.subscribe_board_params(board.slot, [param_name])
                      bd_values[param_name] = param_value[0]
                    except Exception as e:
                      logger.error(f'BD_PARAM {board.slot}, {param_name}, {param_prop.type.name} {e}')
                logger.debug(buf)
                for ch in range(board.n_channel):
                  buf = f'{board.slot}-{ch}'
                  ch_params = device.get_ch_param_info(board.slot, ch)
                  ch_values = dict()
                  ch_name = device.get_ch_name(board.slot, [ch])[0]
                  for param_name in ch_params:
                    param_prop = device.get_ch_param_prop(board.slot, ch, param_name)
                    if param_prop.mode is not hv.ParamMode.WRONLY:
                      try:
                        param_value = device.get_ch_param(board.slot, [ch], param_name)
                        buf += f' {param_name}, {param_prop.type.name} {param_value[0]}'
                        # device.subscribe_channel_params(board.slot, ch, [param_name])
                        ch_values[param_name] = param_value[0]
                      except Exception as e:
                        print(e)
                  logger.debug(buf)
                  sql = """
                  INSERT INTO caenhv (
                  timestamp, ip_address, crate_type, board_slot, board_name, board_status,
                  channel, channel_name, v0set, i0set, vmon, imon,
                  rup, rdown, pw, channel_status ) VALUES (
                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s );
                  """
                  val = [now, 'caenhv2', systype, board.slot,
                         board.model + board.description, bd_values['BdStatus'], ch,
                         ch_name, ch_values['V0Set'],
                         ch_values['I0Set'], ch_values['VMon'], ch_values['IMon'],
                         ch_values['RUp'], ch_values['RDWn'], (ch_values['Pw']==1),
                         ch_values['Status']]
                  cur.execute(sql, val)
          time.sleep(10)
  except KeyboardInterrupt:
    pass

#______________________________________________________________________________
if __name__ == '__main__':
  main()
