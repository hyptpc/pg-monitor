-- MPPC HV monitor imported from raspi-mppchv (module/mppchv.py).
-- The 2025 table (PRIMARY KEY timestamp only, channel 0 only) is kept as mppchv_2025.
CREATE TABLE mppchv (
    timestamp           TIMESTAMPTZ NOT NULL,
    controller          TEXT        NOT NULL,  -- raspi-mppchv db suffix without _YYYYMon, e.g. raspi1, BHT_BLCVth
    port                INTEGER     NOT NULL,  -- raspi-mppchv port_id
    vmon                REAL,                  -- V
    imon                REAL,                  -- mA
    hvon                BOOLEAN,
    status_raw          INTEGER,
    temp                REAL,                  -- degC
    overcurrent         BOOLEAN,
    current_out_of_spec BOOLEAN,
    temp_sensor         BOOLEAN,
    temp_in_range       BOOLEAN,
    temp_correction     BOOLEAN,
    PRIMARY KEY (controller, port, timestamp)
);

SELECT create_hypertable('mppchv', 'timestamp');
