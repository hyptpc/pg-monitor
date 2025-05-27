CREATE TABLE mppchv (
    timestamp   TIMESTAMPTZ NOT NULL,
    host        TEXT,
    channel     INTEGER NOT NULL,
    hvon        BOOLEAN,
    overcurrent BOOLEAN,
    vmon        REAL,
    vset        REAL,
    imon        REAL,
    temp        REAL,
    PRIMARY KEY (timestamp)
);

SELECT create_hypertable('mppchv', 'timestamp', migrate_data => TRUE);
