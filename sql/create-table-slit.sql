CREATE TABLE slit
(timestamp   TIMESTAMPTZ NOT NULL DEFAULT now(),
 -- raw unit is [V]
 ifh_minus_raw   REAL,
 ifh_plus_raw    REAL,
 ifv_minus_raw   REAL,
 ifv_plus_raw    REAL,
 mom_minus_raw   REAL,
 mom_plus_raw    REAL,
 mass1_minus_raw REAL,
 mass1_plus_raw  REAL,
 -- cor unit is [mm]
 ifh_minus_cor   REAL,
 ifh_plus_cor    REAL,
 ifv_minus_cor   REAL,
 ifv_plus_cor    REAL,
 mom_minus_cor   REAL,
 mom_plus_cor    REAL,
 mass1_minus_cor REAL,
 mass1_plus_cor  REAL
);

SELECT create_hypertable('slit', 'timestamp', migrate_data => true);
