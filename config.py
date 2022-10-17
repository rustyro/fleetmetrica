import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

env = os.getenv("ENV", os.getenv("APP_SETTINGS", "local"))  # get environment

if env not in ["serverless"]:
    dotenv_path = os.path.join(
        os.path.dirname(__file__), "envs", f"{env}.env"
    )  # determine .env path

    # Load settings variables using dotenv
    load_dotenv(verbose=True, dotenv_path=dotenv_path)


PGDATABASE = os.getenv("PGDATABASE", "fleetmetrica")
PGUSER = os.getenv("PGUSER")
PGPASSWORD = os.getenv("PGPASSWORD")
PGHOST = os.getenv("PGHOST")
PGPORT = int(os.getenv("PGPORT", 5432))
PG_LOG_TABLE = os.getenv("PG_LOG_TABLE", "logs")
BASE_DB_URL = f'postgresql://{PGHOST}:{PGPORT}?user={PGUSER}&password='
BASE_DB_URL = BASE_DB_URL if not PGPASSWORD else f"{BASE_DB_URL}{PGPASSWORD}"
PG_DB_URL = f'postgresql://{PGHOST}:{PGPORT}/{PGDATABASE}?user={PGUSER}&password='
PG_DB_URL = PG_DB_URL if not PGPASSWORD else f"{PG_DB_URL}{PGPASSWORD}"
db = create_engine(BASE_DB_URL)
IS_LAMBDA = True if os.getenv("AWS_LAMBDA_FUNCTION_VERSION", None) else False
LOG_FILE_END_PATH = os.getenv("LOG_FILE_PATH", "logs.csv")
LOG_FILE_PATH = f"/tmp/{LOG_FILE_END_PATH}" if IS_LAMBDA else LOG_FILE_END_PATH

# AWS
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "fleetmetrica")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")




