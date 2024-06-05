#!/usr/bin/env python3

import epics

def alert_me(pvname=None, char_value=None, **kw):
  print(f'Alert! {pvname} = {char_value}')

if __name__ == '__main__':
  a = epics.Alarm(pvname='HDPS:K18BRD5:CMON',
                  trip_point=0.0)
