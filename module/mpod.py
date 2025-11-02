from datetime import datetime
import json
import logging
import html.parser
import math
import pytz
import psycopg2
import requests
import time

from bs4 import BeautifulSoup

from myenv import db_config, get_logger

logger = get_logger('mpod')

ip_address = 'mpod2.monitor.k18br'

#______________________________________________________________________________
def run():
  while True:
    try:
      timestamp = datetime.now(pytz.timezone('Asia/Tokyo'))
      data = fetch_mpod_status(url=f'http://{ip_address}/')
      mainframe_status = data.get('Mainframe Status', 'UNKNOWN')
      logger.debug(data)
      rows = []
      rows.append((
        timestamp,
        ip_address,
        'Mainframe',
        mainframe_status,
        math.nan,
        math.nan,
        math.nan,
        math.nan,
        math.nan,
      ))
      for channel, ch_data in data['Channels'].items():
        rows.append((
          timestamp,
          ip_address,
          channel,
          ch_data['Status'],
          ch_data['Voltage'],
          ch_data['Current'],
          ch_data['Measured Sense Voltage'],
          ch_data['Measured Current'],
          ch_data['Measured Terminal Voltage'],
        ))
      logger.debug(rows)
      with psycopg2.connect(**db_config) as conn:
        with conn.cursor() as cur:
          cur.executemany("""
          INSERT INTO mpod (
          timestamp, ip_address, channel, status,
          vset, iset, vmons, imon, vmont)
          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
          """, rows)
          conn.commit()
    except Exception as e:
      logger.error(e)
    time.sleep(4)

#______________________________________________________________________________
def fetch_mpod_status(url):
  ret = requests.get(url, timeout=5)
  ret.raise_for_status()
  soup = BeautifulSoup(ret.text, 'html.parser')
  tables = soup.find_all("table", {"id": "tab"})
  data_dict = {}
  for table in tables:
    caption = table.find("caption")
    if not caption:
      continue
    title = caption.text.strip()
    # Mainframe Status
    if title == "Global Status":
      rows = table.find_all("tr")
      for row in rows:
        cells = [td.text.strip() for td in row.find_all("td")]
        if len(cells) == 2 and cells[0] == "Mainframe Status":
          data_dict["Mainframe Status"] = cells[1]
    # Output Channels
    elif title == "Output Channels":
      headers = [th.text.strip() for th in table.find_all("th")]
      channels = {}
      for row in table.find_all("tr")[1:]:
        cells = [td.text.strip() for td in row.find_all("td")]
        if len(cells) == len(headers):
          ch_name = cells[0].replace(' ', '')
          channel_data = {}
          for header, cell in zip(headers[1:], cells[1:]):
            try:
              val = float(cell.split()[0])
              unit = cell.split()[1]
              if 'u' in unit:
                val = val * 1e-6
              elif 'm' in unit:
                val = val * 1e-3
            except (ValueError, IndexError):
              val = cell
            channel_data[header] = val
          channels[ch_name] = channel_data
      data_dict["Channels"] = channels
  return data_dict

#______________________________________________________________________________
if __name__ == '__main__':
  run()
