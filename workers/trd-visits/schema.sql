-- trd-visits D1 schema. Anonymous: no IP, no user agent, no cookies. A visit id is random and lives 30 min.
CREATE TABLE IF NOT EXISTS hits (
  visit     TEXT    NOT NULL,          -- random 16-hex id from assets/trd/visit.js
  seq       INTEGER NOT NULL,          -- order within the visit
  ts        INTEGER NOT NULL,          -- ms since epoch (server clock)
  type      TEXT    NOT NULL,          -- view | leave | hide | event
  path      TEXT,
  room      TEXT,
  ms        INTEGER,                   -- visible time on the page (leave/hide)
  ref       TEXT,                      -- referrer host, first view only
  source    TEXT, medium TEXT, campaign TEXT,   -- utm_*, first view only
  dev       TEXT,                      -- phone | desktop, first view only
  event     TEXT, platform TEXT, item TEXT,     -- share taps etc.
  PRIMARY KEY (visit, seq)
);
CREATE INDEX IF NOT EXISTS hits_ts ON hits(ts);
CREATE INDEX IF NOT EXISTS hits_type_ts ON hits(type, ts);
