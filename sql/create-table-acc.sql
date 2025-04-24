CREATE TABLE acc (
  timestamp          TIMESTAMPTZ NOT NULL DEFAULT now(),
  run_no             INTEGER,
  shot_no            INTEGER,
  mr_cycle           REAL,
  mr_power           REAL,
  opr_mode           TEXT,
  mr_p3_intensity    REAL,
  syim_power         REAL,
  syim_intensity     REAL,
  bdmpim_intensity   REAL,
  sx_duty            REAL,
  sx_ext_effi        REAL,
  sx_splen           REAL,
  t1_mean_x          REAL,
  t1_mean_y          REAL,
  t1_sigma_x         REAL,
  t1_sigma_y         REAL,
  PRIMARY KEY(timestamp)
);

SELECT create_hypertable('acc', 'timestamp', migrate_data => true);
