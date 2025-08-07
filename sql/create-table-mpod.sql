CREATE TABLE mpod (
    timestamp TIMESTAMPTZ NOT NULL,
    ip_address TEXT,
    channel TEXT NOT NULL,
    status TEXT,
    vset REAL,
    iset REAL,
    vmons REAL,
    imon REAL,
    vmont REAL,
    PRIMARY KEY (timestamp, channel)
);

SELECT create_hypertable('mpod', 'timestamp');
