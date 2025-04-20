CREATE TABLE dhcp (
  timestamp     TIMESTAMPTZ NOT NULL DEFAULT now(),
  ip_address    INET        NOT NULL,
  mac_address   TEXT,
  vendor        TEXT,
  interface     TEXT,
  hostname      TEXT, -- short hostname (e.g. vme01)
  domain        TEXT, -- domain name (e.g. daq.k18br)
  status        BOOLEAN,
  PRIMARY KEY (ip_address, interface, timestamp)
);
