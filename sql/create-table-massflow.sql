CREATE TABLE massflow (
  timestamp     TIMESTAMPTZ NOT NULL DEFAULT now(),
  hostname      TEXT,
  gas_type	TEXT,
  status        BOOLEAN,
  svalve	TEXT,
  ivalve	REAL,
  fset		REAL,
  fmon		REAL,
  total		REAL,
  alarm		INTEGER,
  PRIMARY KEY (timestamp, hostname)
);
