CREATE TABLE shs (
    timestamp TIMESTAMPTZ PRIMARY KEY NOT NULL DEFAULT now(),
    ai_tcx01 REAL,
    ai_tcx02 REAL,
    ai_tcx03 REAL,
    ai_tcx04 REAL,
    ai_tcx05 REAL,
    ai_tcx06 REAL,
    ai_tcx07 REAL,
    ai_tcx08 REAL,
    ai_tsd09 REAL,
    ai_tsd10 REAL,
    ai_tsd11 REAL,
    ai_tsd12 REAL,
    ia_tcx01 REAL,
    ia_tcx02 REAL,
    ia_tcx03 REAL,
    ia_tcx04 REAL,
    ia_tcx05 REAL,
    ia_tcx06 REAL,
    ia_tcx07 REAL,
    ia_tcx08 REAL,
    ia_tsd09 REAL,
    ia_tsd10 REAL,
    ia_tsd11 REAL,
    ia_tsd12 REAL,
    ai_tcc13 REAL,
    ai_tcc14 REAL,
    ai_tcc15 REAL,
    ai_tcc16 REAL,
    ai_tcc17 REAL,
    ai_tcc18 REAL,
    ai_tcc19 REAL,
    ai_tcc20 REAL,
    ai_ci_ps REAL,
    ai_v_hall REAL,
    ia_v_hall REAL
);

SELECT create_hypertable('shs', 'timestamp', migrate_data => true);
