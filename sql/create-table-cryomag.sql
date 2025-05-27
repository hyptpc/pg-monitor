CREATE TABLE cryomag ( -- SHS Power Supply
    timestamp TIMESTAMPTZ PRIMARY KEY NOT NULL DEFAULT now(),
    iout        REAL,   -- Output current (A)
    imag        REAL,   -- Magnet current (A)
    vout        REAL,   -- Output voltage (V)
    vmag        REAL,   -- Magnet voltage (V)
    sweep       TEXT,   -- Sweep status ("sweep up", "idle")
    mode        TEXT,   -- Operation mode ("Manual", "Shim")
    ps_heater   BOOLEAN -- Persistent heater ON/OFF (true=ON)
);

SELECT create_hypertable('cryomag', 'timestamp', migrate_data => true);
