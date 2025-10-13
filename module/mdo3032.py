"""
MDO3032 continuous capture (CH1 only)

- Hide UI clutter (cursor/grid/menu/measurements, etc.) to speed up redraw
- CH1: 200 mV/div, trigger level +30 mV (rising edge, NORMAL mode)
- Horizontal position shifted by -3.0 div (≈2nd division from the left)
- Loop forever: single arm -> wait for trigger -> JPEG hardcopy -> save -> webhook -> re-arm
- Log trigger level and horizontal position every shot
"""

import os
import time
import datetime as dt
from pathlib import Path
import pyvisa
import requests
from typing import Optional

from myenv import db_config, get_logger

module_name = os.path.splitext(os.path.basename(__file__))[0]
logger = get_logger(module_name)

# ====== User settings ======
SCOPE_IP   = "192.168.20.30"          # scope IP address
BACKEND    = "@py"                    # use "@ni" if NI-VISA is available
SAVE_DIR   = Path("/home/oper/share/spark") # absolute path to save directory
POLL_S     = 0.03                     # polling interval to wait for trigger
H_POS_DIV  = -3.0                     # horizontal position in divisions from center
# ===========================

rm = None # resource manager
inst = None # main instrument object

#______________________________________________________________________________
def now_name():
  return dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

#______________________________________________________________________________
def open_scope():
  global rm
  rm = pyvisa.ResourceManager(BACKEND)
  global inst
  inst = rm.open_resource(f"TCPIP::{SCOPE_IP}::INSTR", timeout=20000)
  # inst = rm.open_resource(f"TCPIP::{SCOPE_IP}::4000::SOCKET", timeout=20000)
  inst.write_termination = "\n"
  inst.read_termination  = "\n"     # newline required for text queries
  inst.chunk_size        = 1024*1024

#______________________________________________________________________________
def lighten_ui():
  """Best-effort: disable UI layers; ignore if a command is unsupported."""
  cmds_try = [
    "DISP:GRAT OFF",      # grid
    "DISP:MENU OFF",      # side menu
    "CURS:STATE OFF",     # cursors
    "MEASU:STAT OFF",     # overall measurements banner
    "MEASU:MEAS1:STATE OFF",
    "MEASU:MEAS2:STATE OFF",
    "MEASU:MEAS3:STATE OFF",
    "MEASU:MEAS4:STATE OFF",
    "DISP:LEGend OFF",    # legend
    "DISP:HUD OFF",       # head-up display
  ]
  for c in cmds_try:
    try: inst.write(c)
    except: pass

#______________________________________________________________________________
def setup_hardcopy():
  """Configure fast JPEG hardcopy over Ethernet."""
  inst.write("; ".join([
    "HARDCOPY:PORT ETHERNET",
    "HARDCOPY:FILEFORMAT JPEG",
    "HARDCOPY:INKSAVER OFF",
    "HARDCOPY:LAYOUT FULLSCREEN",
    "HARDCOPY:PREVIEW OFF",
    "HARDCOPY:PALETTE COLOR"
  ]))

#______________________________________________________________________________
def setup_ch1_and_trigger():
  """Set up CH1 scaling and trigger conditions."""
  inst.write("SEL:CH1 ON")
  inst.write("CH1:SCALE 0.2")      # 200 mV/div
  try:
    inst.write("CH1:POS 0.0")    # vertical center
  except:
    pass

  inst.write("TRIG:A:TYPE EDGE")
  inst.write("TRIG:A:EDGE:SOUR CH1")
  inst.write("TRIG:A:EDGE:SLOP RIS")
  try:
    inst.write("TRIG:A:LEVel CH1,0.15")  # +150 mV
  except:
    inst.write("TRIG:A:LEVel 0.15")
  try:
    inst.write("TRIG:A:MOD NORM")        # NORMAL (not AUTO)
  except:
    inst.write("TRIG:MODE NORM")

#______________________________________________________________________________
def _div_to_pretrigger_percent(div_from_center: float) -> float:
    """
    Convert horizontal position in divisions from center to pre-trigger percent.
    Screen width = 10 div; 0% = very left, 50% = center, 100% = very right.
    percent = (5 + div_from_center) * 10
    """
    pct = (5.0 + div_from_center) * 10.0
    # clamp to [0, 100] just in case
    return max(0.0, min(100.0, pct))

#______________________________________________________________________________
def finalize():
  if inst is not None:
    try:
      inst.close()
    except Exception:
      pass
  try:
    rm.close()
  except Exception:
    pass
  logger.info('close')

#______________________________________________________________________________
def set_horizontal_position(div=H_POS_DIV):
  """
  On MDO3032 the effective control is pre-trigger percent, not HOR:POS.
  We convert 'div from center' to percent and set HOR:POSition <pct>.
  """
  pct = _div_to_pretrigger_percent(div)
  # try to ensure we are on main timebase and not zoom/delay
  for cmd in ("HOR:MODE MAIN", "HOR:DEL:STATE OFF", "DISP:ZOOM:STATE OFF"):
    try: inst.write(cmd)
    except: pass
  inst.write(f"HOR:POSition {pct}")
  try:
    applied = inst.query("HOR:POSition?").strip()
    logger.info(f"Horizontal pretrigger = {applied} %  (request={pct:.1f}%)")
  except Exception:
    logger.warning("HOR:POSition? readback failed.")
    applied = None
  return applied

#______________________________________________________________________________
def single_arm():
  """Arm the scope for a single acquisition."""
  inst.write("ACQ:STOPA SEQ")
  inst.write("ACQ:STATE RUN")

#______________________________________________________________________________
def wait_trigger(poll=POLL_S):
  """Wait indefinitely until acquisition stops (ACQ:STATE? == 0)."""
  while True:
    try:
      if inst.query("ACQ:STATE?").strip() == "0":
        return
    except:
      pass
    time.sleep(poll)

#______________________________________________________________________________
def grab_jpeg() -> bytes:
  """Perform HARDCOPY and return JPEG bytes (safe termination flip)."""
  inst.write("HARDCOPY START")
  # switch to raw for binary read, then restore
  old_term = inst.read_termination
  inst.read_termination = None
  data = inst.read_raw()
  inst.read_termination = old_term
  return data

#______________________________________________________________________________
def read_trigger_level() -> Optional[float]:
  """Read back the actual (quantized) trigger level."""
  for cmd in ("TRIG:A:LEV?", "TRIG:LEV?", "TRIG:MAIn:LEV?"):
    try:
      return float(inst.query(cmd).strip())*1.e3
    except:
      continue
  return None

#______________________________________________________________________________
def initialize():
  global outdir
  open_scope()
  logger.info(f'Connected: {inst.query("*IDN?").strip()}')
  # One-time initialization
  try: inst.write("*CLS")
  except: pass
  lighten_ui()
  setup_hardcopy()
  setup_ch1_and_trigger()
  # Apply and verify horizontal shift (via pre-trigger %)
  pos = set_horizontal_position(H_POS_DIV)

#______________________________________________________________________________
def run():
  t0 = time.time()
  # Arm and wait
  single_arm()
  wait_trigger()
  t_wait = time.time() - t0
  # Capture
  t1 = time.time()
  jpg = grab_jpeg()
  out = SAVE_DIR / f"mdo_{now_name()}.jpg"
  out.write_bytes(jpg)
  t_grab = time.time() - t1
  # Read back trigger level every shot
  vth = read_trigger_level()
  vth_str = f"{vth:.1f} mV" if vth is not None else "N/A"
  # Read back horizontal percent (cheap; useful for logs)
  try:
    pos_now = inst.query("HOR:POSition?").strip()
  except Exception:
    pos_now = "N/A"
  logger.debug(f"saved {out.name}  size={len(jpg)}  "
               f"wait={t_wait:.2f}s  grab={t_grab:.2f}s  trig={vth_str}")
  return t1, out, vth

#______________________________________________________________________________
def main():
  initialize()
  while True:
    try:
      run()
    except KeyboardInterrupt:
      break

#______________________________________________________________________________
if __name__ == "__main__":
  main()
