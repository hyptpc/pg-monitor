-- E72 rawdata on KEKCC HSM, from ls-kekcc.txt (module/kekcc.py).
CREATE TABLE kekcc_rawdata (
  timestamp          TIMESTAMPTZ NOT NULL DEFAULT now(),
  run_number         INTEGER PRIMARY KEY,
  size_bytes         BIGINT,
  mtime              TIMESTAMPTZ,
  readonly           BOOLEAN
);

-- When the listing was taken (single row).
CREATE TABLE kekcc_status (
  id                 INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
  timestamp          TIMESTAMPTZ NOT NULL DEFAULT now(),
  listed_at          TIMESTAMPTZ,
  n_files            INTEGER
);
