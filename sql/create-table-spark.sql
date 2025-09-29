CREATE TABLE spark ( -- HypTPC Spark
    timestamp TIMESTAMPTZ PRIMARY KEY NOT NULL DEFAULT now(),
    -- ip_address TEXT,
    filepath  TEXT,
    voltage   REAL,
    threshold REAL
);

SELECT create_hypertable('spark', 'timestamp', migrate_data => true);
