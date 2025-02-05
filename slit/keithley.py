import serial_instrument
import serial
import time

#______________________________________________________________________________
class Keithley(serial_instrument.SerialInstrument):
  def __init__(self, port="/dev/ttyUSB1", baud=9600):
    super().__init__(port, baud, parity=serial.PARITY_NONE,
                     bytesize=8, stopbits=1, timeout=1)
    self.id_string = "KEITHLEY INSTRUMENTS INC.,MODEL 2700,0822752,B02"
    self.manufacturer = 'Keithley'
    self.model_number = '2700'
    self.description  = 'Multimeter'
    self.idn()
    self._reset()

  def _reset(self):
    self.write("*RST")
    self.write("*OPC?")
    result = self.serial.readline()

  def setup_scan(self, nchans=10,remove=2):
    self.write("FORM SRE")
    self.write("FORM:ELEM READ")
    self.write("SYST:TST:TYPE RTCL\nSYST:BEEP 0")
    self.write("TRAC:CLE")
    self.write("INIT:CONT OFF")
    self.write("TRIG:SOUR IMM\nTRIG:COUN 1\nSAMP:COUN %02d"%nchans)
    self.write("ROUT:SCAN (@101:1%02d)"%nchans)
    self.write("ROUT:SCAN:TSO IMM")
    self.write("ROUT:SCAN:LSEL INT")
    self.ask("*OPC?")
    self.remove = remove
    result = self.serial.readline()

  def ask(self,command):
    self.write(command)
    result=self.serial.readline()
    return result[1:-2]

  def ask_slow(self,command):
    self.write(command)
    self.write("*OPC?")
    result=self.serial.readline()
    return result

  def scan(self):
    self.write("READ?")
    time.sleep(2)
    result=self.serial.readline()
    #print result
    #print str(result[1:-1*self.remove])
    #print str(result[1:-1*self.remove]).strip()
    #print str(result[1:-1*self.remove]).strip().replace('+','')
    return str(result[1:-1*self.remove]).strip().replace('+','')

if __name__ == '__main__':
  k=Keithley(port='/dev/ttyUSB0')
  k.setup_scan()    
  while True:
    print('---------')
    time.sleep(2)
    print(k.scan())
