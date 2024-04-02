#!/usr/bin/env python3

__author__ = 'Shuhei Hayakawa'

import datetime
import logging
import psycopg
import re
import threading
import time

logger = logging.getLogger('__main__').getChild(__name__)

class DHCP:
  def __init__(self, interval=10):
    self.interval = interval
    self.dhcp_conf_path = '/misc/sbc-etc-dhcp/dhcpd.conf'
    self.dhcp_leases_path = '/misc/sbc-var-dhcpd/dhcpd.leases'
    self.db_connection_info = {
      'dbname': 'e73',
      'user': 'postgres',
      'password': 'pg',
      'host': 'localhost',
      'port': '5432'
    }
    self.hosts = dict()
    self.will_stop = False

  def __parse_dhcp_conf(self):
    with open(self.dhcp_conf_path, 'r') as f:
      matches = re.findall(r'\nhost\s+(\S+)\s*{\s*next-server 192.168.1.201;'+
                           r'\s*hardware\s+ethernet\s+(\S+)\s*;'+
                           r'\s*fixed-address\s+(\S+)\s*;', f.read())
      for match in matches:
        self.hosts[match[2]] = {'host_name': match[0], 'mac_address': match[1]}
      logger.debug(self.hosts)

  def __parse_dhcp_leases(self):
    with open(self.dhcp_leases_path, 'r') as f:
      matches = re.findall(r'\nlease\s+(\S+)\s*{(?:[^}]*\n\s*)*?'+
                           r'starts\s+(\S+)\s+(\S+)\s+(\S+);\s*(?:[^}]*\n\s*)*?'+
                           r'ends\s+(\S+)\s+(\S+)\s+(\S+);\s*(?:[^}]*\n\s*)*?'+
                           r'binding\s+state\s+(\S+);\s*(?:[^}]*\n\s*)*?'+
                           r'hardware\s+ethernet\s+(\S+)\s*;',
                           f.read())
      for match in matches:
        self.hosts[match[0]] = {'start_time': datetime.datetime.strptime(match[2]+match[3]+'+0900', '%Y/%m/%d%H:%M:%S%z'),
                                'end_time': datetime.datetime.strptime(match[5]+match[6]+'+0900', '%Y/%m/%d%H:%M:%S%z'),
                                'state': match[7],
                                'mac_address': match[8]}

  def __insert_hosts_to_postgres(self):
    conn = None
    try:
      conn = psycopg.connect(**self.db_connection_info)
      cur = conn.cursor()
      for ip in self.hosts:
        host = self.hosts[ip]
        host_name = host['host_name'] if 'host_name' in host else ''
        start_time = host['start_time'] if 'start_time' in host else None
        end_time = host['end_time'] if 'end_time' in host else None
        state = host['state'] if 'state' in host else None
        mac_address = host['mac_address'] if 'mac_address' in host else None
        tap = (ip, host_name, start_time, end_time, state, mac_address)
        cur.execute("INSERT INTO dhcp_hosts (ip_address, host_name, start_time, end_time, state, mac_address) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (ip_address) DO UPDATE SET host_name=EXCLUDED.host_name, start_time=EXCLUDED.start_time, end_time=EXCLUDED.end_time, state=EXCLUDED.state, mac_address=EXCLUDED.mac_address;", tap)
        logger.debug(f'{tap}')
    except (psycopg.Error or psycopg.OperationalError) as e:
      if conn is not None:
        conn.rollback()
      logger.error(e)
      return
    except KeyboardInterrupt:
      return
    conn.commit()
    cur.close()
    conn.close()

  def __updater(self):
    self.__parse_dhcp_conf()
    self.__parse_dhcp_leases()
    self.__insert_hosts_to_postgres()

  def run(self):
    base_time = time.time()
    next_time = 0
    while not self.will_stop:
      try:
        t = threading.Thread(target=self.__updater)
        t.daemon = True
        t.start()
        t.join()
        next_time = ((base_time - time.time()) % self.interval) or self.interval
        time.sleep(next_time)
      except KeyboardInterrupt:
        break

  def start(self):
    logger.debug('start')
    t = threading.Thread(target=self.run)
    t.daemon = True
    t.start()

  def stop(self):
    logger.debug('stop')
    self.will_stop = True

d = DHCP()

def start():
  d.start()

def stop():
  d.stop()

if __name__ == '__main__':
  d = DHCP()
  d.run()
