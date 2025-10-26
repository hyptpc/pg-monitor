CREATE TABLE caenhv (
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    ip_address   TEXT,
    crate_type   TEXT,
    board_slot   INTEGER,
    board_name   TEXT,
    board_status TEXT,
    channel      INTEGER,
    channel_name TEXT NOT NULL,
    v0set        REAL,
    i0set        REAL,
    vmon        REAL,
    imon        REAL,
    rup          REAL,
    rdown        REAL,
    pw           BOOLEAN,
    channel_status   TEXT,
    -- PRIMARY KEY (timestamp, channel_name)
);

SELECT create_hypertable('caenhv', 'timestamp', migrate_data => true);

