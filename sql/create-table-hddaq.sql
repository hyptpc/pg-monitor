CREATE TABLE hddaq
(timestamp                      TIMESTAMP WITH TIME ZONE,
 run_number                     INTEGER,
 event_number                   INTEGER,
 start_time                     TIMESTAMP WITH TIME ZONE,
 comment                        TEXT,
 CONSTRAINT hddaq_pkey PRIMARY KEY (run_number)
);
