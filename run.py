#!/usr/bin/env python3

__author__ = 'Shuhei Hayakawa'

'''
Run script for slow monitor system using PostgreSQL database
'''

import logging
import logging.config
import os
import threading
import signal
import sys
import yaml

top_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(top_dir, 'module'))

''' modules '''
import accelerator
import apiste
import beam
import caenhv
import dhcp
import ess
import field
import gl840
import hddaq
import kikusui
import magnet
import scaler

logger = logging.getLogger(__name__)
modules = [accelerator, apiste, beam,
           caenhv, dhcp, ess, field, gl840, hddaq, kikusui,
           magnet, scaler]

#________________________________________________________________
def signal_handler(signum, frame):
  print()
  logger.info('catch signal')
  logger.info('waiting for all threads to be finalized')
  for m in modules:
    m.stop()

#______________________________________________________________________________
def run():
  if not os.path.exists(os.path.join(top_dir, 'log')):
    print('Plese prepare log directory.')
    return
  log_conf = os.path.join(top_dir, 'logging_config.yml')
  with open(log_conf, 'r') as f:
    logging.config.dictConfig(yaml.safe_load(f))
  for m in modules:
    m.start()
  signal.signal(signal.SIGINT, signal_handler)
  logger.info('start')
  thread_list = threading.enumerate()
  thread_list.remove(threading.main_thread())
  for t in thread_list:
    t.join()
  logger.info('bye')

#______________________________________________________________________________
if __name__ == '__main__':
  run()
  
