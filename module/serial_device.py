#!/usr/bin/env python

import serial
import time

#______________________________________________________________________________
class SerialDevice(object):
  def __init__(self, port, baud=9600, parity='N', bytesize=8,
               stopbits=1, timeout=1):
    super().__init__()
    self.port = port
    self.baud = baud
    self.manufacturer = ""
    self.model_number = ""
    self.description  = ""
    self.serial = None
    try:
      self.serial = serial.Serial(
        port = port,
        baudrate = baud,
        parity = parity,
        bytesize = bytesize,
        stopbits = stopbits,
        timeout = 1,
        rtscts = False,
        dsrdtr = False
      )
      # print(self.serial, self.idn())
    except serial.serialutil.SerialException:
      print("WARNING: serial port could not be found!")

  def identify(self):
    identify_string = f'{self.manufacturer}, {self.model_number}'
    return identify_string

  def write(self, command):
    tmpcmd = command + '\r\n'
    result = self.serial.write(tmpcmd.encode())

  def ask(self,command):
    self.write(command)
    result = self.serial.readline()
    return result.decode().strip().replace('+', '')

  def idn(self):
    result = self.ask("*IDN?")
    return result

if __name__ == '__main__':
  ser = SerialDevice('/dev/ttyUSB0')
  print(ser.idn())
