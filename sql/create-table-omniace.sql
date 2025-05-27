CREATE TABLE omniace (
    timestamp TIMESTAMPTZ PRIMARY KEY NOT NULL DEFAULT now(),
    ch01 REAL,
    ch02 REAL,
    ch03 REAL,
    ch04 REAL,
    ch05 REAL,
    ch06 REAL,
    ch07 REAL,
    ch08 REAL,
    ch09 REAL,
    ch10 REAL,
    ch11 REAL,
    ch12 REAL,
    ch13 REAL,
    ch14 REAL,
    ch15 REAL,
    ch16 REAL,
    ch17 REAL,
    ch18 REAL
);

SELECT create_hypertable('omniace', 'timestamp', migrate_data => true);
