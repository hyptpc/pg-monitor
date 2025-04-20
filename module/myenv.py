import logging

db_config = {
  'host': 'localhost',
  'port': 5432,
  'dbname': 'e72',
  'user': 'oper',
  'password': 'himitsu'
}

def get_logger(name: str = "default", level=logging.INFO) -> logging.Logger:
  logger = logging.getLogger(name)
  if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
      '(%(name)s) [%(levelname)s] %(message)s',
      # datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
  return logger
