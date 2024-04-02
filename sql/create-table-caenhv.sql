CREATE TABLE caenhv
(timestamp   TIMESTAMP WITH TIME ZONE,
 ip_address   TEXT,
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
