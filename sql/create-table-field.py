CREATE TABLE field ( -- Magnetic Field
    timestamp TIMESTAMPTZ PRIMARY KEY NOT NULL DEFAULT now(),
    name        TEXT,
    field       REAL -- [T]
);

SELECT create_hypertable('field', 'timestamp', migrate_data => true);
