CREATE TABLE hddaq (
  timestamp          TIMESTAMPTZ NOT NULL DEFAULT now(),
  run_number         INTEGER PRIMARY KEY,
  start_time         TIMESTAMPTZ,
  stop_time          TIMESTAMPTZ,
  comment            TEXT,
  recorder           BOOLEAN,
  event_number       INTEGER,
  data_size_bytes    BIGINT
);

-- SELECT create_hypertable('hddaq', 'timestamp', migrate_data => true);
