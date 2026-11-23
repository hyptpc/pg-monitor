CREATE TABLE IF NOT EXISTS target (
  timestamp        timestamptz PRIMARY KEY,
  temp_ref1st      double precision,
  temp_cond_up     double precision,
  temp_cond_dw     double precision,
  temp_tgt_up      double precision,
  temp_tgt_dw      double precision,
  temp_room        double precision,
  h2_press         double precision,
  heater_v         double precision,
  vac_cryo         double precision,
  vac_tank         double precision,
  press_diff       double precision,
  h2leak_1         double precision,
  h2leak_2         double precision,
  h2leak_3         double precision,
  fan_on           boolean,
  ref_on           boolean,
  alert_ybox       boolean,
  alert_gl860      boolean,
  alert_h2leak     boolean,
  alert_user       boolean,
  hdexhaust_flow   double precision
);

SELECT create_hypertable('target', 'timestamp', migrate_data => true);
