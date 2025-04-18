CREATE TABLE ess (
  timestamp  TIMESTAMPTZ PRIMARY KEY,
  neg_vset1  REAL,
  neg_vmon1  REAL,
  neg_imon1  REAL,
  pos_vset1  REAL,
  pos_vmon1  REAL,
  pos_imon1  REAL,
  ccg_pmon1  REAL,
  neg_vset2  REAL,
  neg_vmon2  REAL,
  neg_imon2  REAL,
  pos_vset2  REAL,
  pos_vmon2  REAL,
  pos_imon2  REAL,
  ccg_pmon2  REAL
);

-- -- for e73
-- CREATE TABLE ess
-- (name  TEXT,
--  timestamp   TIMESTAMP WITH TIME ZONE,
--  electrode   TEXT,
--  vset        REAL,
--  vmon        REAL,
--  imon        REAL,
--  vacuum      REAL
-- );
