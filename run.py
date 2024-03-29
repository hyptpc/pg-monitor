#!/usr/bin/env python3

import logging
import logging.config
import os
import subprocess
import threading
import signal
import sys
import yaml

import apiste
import caenhv
import dhcp
import ess
import gl840
import kikusui

top_dir = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    print()
    logger.info('catch signal')
    apiste.stop()
    caenhv.stop()
    dhcp.stop()
    ess.stop()
    gl840.stop()
    kikusui.stop()
    logger.info('waiting for all threads to be finalized')
    thread_list = threading.enumerate()
    thread_list.remove(threading.main_thread())
    for t in thread_list:
      t.join()
    logger.info('bye')
    sys.exit()

if __name__ == '__main__':
  log_conf = os.path.join(top_dir, 'logging_config.yml')
  with open(log_conf, 'r') as f:
    logging.config.dictConfig(yaml.safe_load(f))

  apiste.start()
  caenhv.start()
  ess.start()
  dhcp.start()
  gl840.start()
  kikusui.start()

  signal.signal(signal.SIGINT, signal_handler)
    
  logger.info('start')

  thread_list = threading.enumerate()
  thread_list.remove(threading.main_thread())
  for t in thread_list:
    t.join()
