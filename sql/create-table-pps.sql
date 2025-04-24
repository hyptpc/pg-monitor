CREATE TABLE pps (
  timestamp           TIMESTAMPTZ NOT NULL DEFAULT now(),
  k18_cntr1_1s        REAL,
  k18_cntr1_intg_hr   REAL,
  k18br_cntr1_1s      REAL,
  k18br_cntr1_intg_hr REAL,
  org0201g	      REAL,
  org0201n	      REAL,
  org0202g	      REAL,
  org0202n	      REAL,
  PRIMARY KEY(timestamp)
);

SELECT create_hypertable('pps', 'timestamp', migrate_data => true);
