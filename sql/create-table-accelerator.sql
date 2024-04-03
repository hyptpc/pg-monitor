CREATE TABLE accelerator -- http://www-cont.j-parc.jp/HD/index
(timestamp                      TIMESTAMP WITH TIME ZONE,
 run_number                     INTEGER,
 shot_number                    INTEGER,
 -- last_shot                      TIMESTAMP WITH TIME ZONE,
 mr_power                       REAL,
 mr_intensity                   REAL,
 mr_cycle                       REAL,
 sx_duty                        REAL,
 sx_spill_length                REAL,
 sx_extraction_efficiency       REAL,
 -- hd_status                      TEXT,
 hd_mode                        TEXT,
 -- hd_mps_setting                 TEXT,
 hd_power_syim                  REAL,
 hd_intensity_syim              REAL,
 hd_intensity_rgicm             REAL
 -- hd_b_intensity_bdmpim          REAL,
 -- hd_b_intensity_bic             REAL
);
