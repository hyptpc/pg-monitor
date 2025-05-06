from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from datetime import datetime
import logging
from rich.logging import RichHandler
from rich import print
import subprocess

log_buffer = []

def append_log(line):
  log_buffer.append(line)
  if len(log_buffer) > 100:
    log_buffer.pop(0)

rich_handler = RichHandler(markup=True, rich_tracebacks=True)
logging.basicConfig(
  level=logging.INFO,
  format="%(message)s",
  datefmt="[%Y-%m-%d %H:%M:%S]",
  handlers=[rich_handler]
)
logger = logging.getLogger("alert")

class AlertHandler(BaseHTTPRequestHandler):
  def do_POST(self):
    content_length = int(self.headers['Content-Length'])
    body = self.rfile.read(content_length)
    try:
      data = json.loads(body)
      status = data.get("status", "unknown").upper()
      now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      logger.info(f"🚨 ALERT STATUS: [bold red]{status}[/bold red]")
      append_log(f"[{now_str}] 🚨 ALERT STATUS: {status}")
      for alert in data.get("alerts", []):
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})
        name = labels.get("alertname", "-")
        summary = annotations.get("summary", "-")
        starts_at = alert.get("startsAt", "-")
        logger.info(f"🔔 Alert Name : [cyan]{name}")
        logger.info(f"📝 Summary    : [yellow]{summary}")
        logger.info(f"🕒 Started At : [blue]{starts_at}")
        append_log(f"[{now_str}] 🔔 {name} | {summary} | {starts_at}")
      if status == 'FIRING':
        subprocess.run(
          ["aplay", "/home/oper/share/pg-monitor/sound/alert_sound.wav"],
          # ["aplay", "-D", "plughw:2,0", "/home/oper/share/pg-monitor/sound/alert_sound.wav"],
          stdout=subprocess.DEVNULL,
          stderr=subprocess.DEVNULL
        )
    except Exception as e:
      now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      logger.error(f"[red]Error parsing alert:[/] {e}")
      append_log(f"[{now_str}] ❌ Error: {e}")
    self.send_response(200)
    self.end_headers()

  def do_GET(self):
    if self.path == "/log":
      self.send_response(200)
      self.send_header("Content-Type", "text/html; charset=utf-8")
      self.end_headers()
      self.wfile.write(b"<html><head><meta http-equiv='refresh' content='5'><style> body { margin: 10px;   font-family: monospace; font-size: 14px; background-color: white; color: black; } @media (prefers-color-scheme: dark) { body { background-color: #111; color: #ddd; } } </style></head><body>")
      self.wfile.write(b"<h2>Alert Log (Last 100)</h2><pre>")
      for line in log_buffer:
        self.wfile.write(line.encode('utf-8') + b"\n")
      self.wfile.write(b"</pre></body></html>")
    else:
      self.send_response(404)
      self.end_headers()

  def log_message(self, format, *args):
    logger.info(f"[dim]HTTP {self.command} {self.path} from {self.client_address[0]}[/dim]")

if __name__ == "__main__":
  try:
    logger.info("[green]Listening on port 9000...[/green]")
    server = HTTPServer(('0.0.0.0', 9000), AlertHandler)
    server.serve_forever()
  except KeyboardInterrupt:
    logger.info("[red]Shutting down server due to keyboard interrupt (Ctrl+C).[/red]")
    server.server_close()
