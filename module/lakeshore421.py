#!/usr/bin/env python3

import serial
import time
import numpy as np
import sys

import serial_instrument

#______________________________________________________________________________
class Lakeshore421(serial_instrument.SerialInstrument):
  def __init__(self, port="/dev/ttyADV1", baud=9600):
    super().__init__(port, baud, parity=serial.PARITY_ODD,
                     bytesize=7, stopbits=1, timeout=1)
    self.id_string = "LSCI,MODEL331S,372167,120407"
    self.manufacturer = 'Lakeshore'
    self.model_number = '331S'
    self.description  = 'Temperature Controller'
    self.port = port
    self.baud = baud
    # print(self.idn())
    # print(self.read())
    # print(self.unit())

  def read(self):
    result = self.ask('FIELD?')
    return result

  def unit(self):
    result = self.ask('UNIT?')
    return result

if __name__ == '__main__':
  l = Lakeshore421()
  print(l.read())
  print(l.unit())
  # print(l.ask('AUTO 0'))
  # print(l.ask('RANGE 0'))
  # print(l.ask('RANGE?'))
  # print(l.ask('AUTO?'))
