from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from datetime import datetime
import logging
from rich.logging import RichHandler
from rich import print
import subprocess

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
      for alert in data.get("alerts", []):
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})
        logger.info(f"🔔 Alert Name : [cyan]{labels.get('alertname', '-')}")
        # logger.info(f"📡 Channel    : [magenta]{labels.get('channel', '-')}")
        logger.info(f"📝 Summary    : [yellow]{annotations.get('summary', '-')}")
        logger.info(f"🕒 Started At : [blue]{alert.get('startsAt', '-')}")
        # logger.info("[dim]----------------------------------------[/dim]")
      if status == 'FIRING':
        subprocess.run(
          ["aplay", "-D", "plughw:2,0", "/home/oper/share/pg-monitor/sound/alert_sound.wav"],
          stdout=subprocess.DEVNULL,
          stderr=subprocess.DEVNULL
        )
    except Exception as e:
      logger.error(f"[red]Error parsing alert:[/] {e}")
    self.send_response(200)
    self.end_headers()

  def log_message(self, format, *args):
    logger.info(f"[dim]HTTP {self.command} {self.path} from {self.client_address[0]}[/dim]")

if __name__ == "__main__":
  logger.info("[green]Listening on port 9000...[/green]")
  server = HTTPServer(('0.0.0.0', 9000), AlertHandler)
  server.serve_forever()
