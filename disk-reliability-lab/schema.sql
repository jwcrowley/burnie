CREATE TABLE IF NOT EXISTS disks (
serial TEXT PRIMARY KEY,
model TEXT,
vendor TEXT,
batch TEXT,
size_bytes INTEGER,
interface TEXT,
first_seen TEXT,
last_test TEXT,
status TEXT,
reliability_score INTEGER
);

CREATE TABLE IF NOT EXISTS tests (
id INTEGER PRIMARY KEY AUTOINCREMENT,
serial TEXT,
device TEXT,
started TEXT,
finished TEXT,
result TEXT
);

CREATE TABLE IF NOT EXISTS smart_history (
id INTEGER PRIMARY KEY AUTOINCREMENT,
serial TEXT,
attribute TEXT,
value INTEGER,
timestamp TEXT
);

CREATE TABLE IF NOT EXISTS latency_anomalies (
id INTEGER PRIMARY KEY AUTOINCREMENT,
serial TEXT,
latency_ms REAL,
timestamp TEXT
);

CREATE TABLE IF NOT EXISTS temperature_history (
id INTEGER PRIMARY KEY AUTOINCREMENT,
serial TEXT,
temperature INTEGER,
timestamp TEXT
);
