CREATE TABLE service (
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  name text NOT NULL,
  status text CHECK (status IN ('active', 'inactive', 'failed', 'unknown')),
  last_log text NOT NULL
);

SELECT create_hypertable('service', 'timestamp', migrate_data => true);
