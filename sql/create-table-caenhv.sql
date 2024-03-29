CREATE TABLE caenhv
(ip_address   TEXT,
 timestamp   TIMESTAMP WITH TIME ZONE,
 crate_type   TEXT,
 board_slot   INTEGER,
 board_name   TEXT,
 board_status TEXT,
 channel      INTEGER,
 channel_name TEXT,
 v0set        REAL,
 i0set        REAL,
 vmon        REAL,
 imon        REAL,
 rup          REAL,
 rdown        REAL,
 pw           BOOLEAN,
 channel_status   TEXT
);
