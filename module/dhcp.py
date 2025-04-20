import logging
import subprocess
import psycopg2
from datetime import datetime, timezone
import time
import socket

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s %(message)s')
logger = logging.getLogger()

db_config = {
  'host': 'localhost',
  'port': 5432,
  'dbname': 'e72',
  'user': 'oper',
  'password': 'himitsu'
}

#-------------------------------
interfaces = ["enp1s0f0"]
sleep_interval = 600
# -----------------------------------

conn = psycopg2.connect(**db_config)
cur = conn.cursor()
previous_online = {} # { (ip, interface): (mac, vendor) }

def run_arp_scan(interface):
  try:
    result = subprocess.check_output([
      "sudo", "arp-scan", "--interface=" + interface, "--localnet"
    ], stderr=subprocess.DEVNULL).decode()
    return result
  except subprocess.CalledProcessError as e:
    return logger.error(e)

def parse_arp_output(output, interface):
  result = {}
  for line in output.splitlines():
    parts = line.split("\t")
    if len(parts) >= 3 and parts[0].startswith("192.168."):
      ip = parts[0].strip()
      mac = parts[1].strip()
      vendor = parts[2].strip()
      result[(ip, interface)] = (mac, vendor)
  return result

def resolve_hostname(ip):
  try:
    fqdn = socket.gethostbyaddr(ip)[0]
    if '.' in fqdn:
      hostname, domain = fqdn.split('.', 1)
    else:
      hostname, domain = fqdn, None
    return hostname, domain
  except Exception:
    return None, None

while True:
  timestamp = datetime.now(timezone.utc)
  current_online = {}
  for iface in interfaces:
    output = run_arp_scan(iface)
    scanned = parse_arp_output(output, iface)
    current_online.update(scanned)
    for (ip, interface), (mac, vendor) in scanned.items():
      hostname, domain = resolve_hostname(ip)
      cur.execute("""
        INSERT INTO dhcp (
        timestamp, ip_address, mac_address, vendor, interface, hostname, domain, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
      """, (timestamp, ip, mac, vendor, interface, hostname, domain, True))
  # offline
  for key, (mac, vendor) in previous_online.items():
    if key not in current_online:
      ip, interface = key
      hostname, domain = resolve_hostname(ip)
      cur.execute("""
        INSERT INTO dhcp (
        timestamp, ip_address, mac_address, vendor, interface, hostname, domain, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
      """, (timestamp, ip, mac, vendor, interface, hostname, domain, False))
  conn.commit()
  logger.info('dhcp updated')
  previous_online = current_online
  time.sleep(sleep_interval)
