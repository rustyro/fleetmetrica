import os
from dataclasses import dataclass
from sqlalchemy import create_engine

PGDATABASE = "fleetmetrica"
PGUSER = "postgres"
PGHOST = "localhost"
PGPORT = 5432
PG_LOG_TABLE = os.getenv("PG_LOG_TABLE", "logs")
BASE_DB_URL = f'postgresql://{PGHOST}:{PGPORT}?user={PGUSER}&password='
PG_DB_URL = f'postgresql://{PGHOST}:{PGPORT}/{PGDATABASE}?user={PGUSER}&password='
db = create_engine(BASE_DB_URL)
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs.csv")
PERFORMANCE = []
DAILY_INCIDENT = []
DAILY_SUMMARY = []
