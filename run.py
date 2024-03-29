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
import apiste
import caenhv
import dhcp
import ess
import gl840
import kikusui

logger = logging.getLogger(__name__)
modules = [apiste, caenhv, dhcp, ess, gl840, kikusui]

#________________________________________________________________
def signal_handler(signum, frame):
  print()
  logger.info('catch signal')
  logger.info('waiting for all threads to be finalized')
  for m in modules:
    m.stop()

def run():
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

if __name__ == '__main__':
  run()
  
