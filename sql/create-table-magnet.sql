CREATE TABLE magnet ( -- http://www-cont.j-parc.jp/HD/magnet/primaryA
  timestamp    TIMESTAMPTZ NOT NULL DEFAULT now(),
  magnet_data  JSONB NOT NULL,
  PRIMARY KEY(timestamp)
);

SELECT create_hypertable('magnet', 'timestamp', migrate_data => true);
