from datetime import datetime, timedelta
import argparse
import sys

from .config import db, PGDATABASE, LOG_FILE_PATH, PG_LOG_TABLE
from cli import config
from .logging import Logger as Logr, log
from sqlalchemy import Table, Column, Integer, DateTime, String, MetaData, Text, inspect, create_engine

sys.stdout = Logr(LOG_FILE_PATH)
parser = argparse.ArgumentParser(
    description='Generate mock trucking data')
parser.add_argument('-f', '--files', nargs='+', help='path to sample files used for generation')
parser.add_argument('-dr', '--date_range', help='Date range for the mock dataset (DDMMYY-DDMMYY)')
parser.add_argument('-ds', '--data_size', default=0, help='Number of records to generate in the dataset')
parser.add_argument('-s', '--store', default=1, type=int, help='Storage location for the generate files')
parser.add_argument('-c', '--config', help='Datasource configuration type')
parser.add_argument('-po', '--patter_options', help='Pattern options')


class CLI(object):

    def __init__(self, args: argparse.Namespace):
        end = datetime.now()
        start = end - timedelta(days=30)
        self.files = getattr(args, "files", None)
        self.date_range = getattr(args, "date_range", f"{start.strftime('%d%m%y')}-{end.strftime('%d%m%y')}")
        self.data_size = getattr(args, "data_size", 2000)
        self.store = getattr(args, "store", "./mock_data")
        self.config = getattr(args, "config", "perfomance")
        self.pattern_options = getattr(args, "pattern_options", "")
        self.db_conn = self.init_db()

    @staticmethod
    def init_db():
        """Initialize a database connection and create the named database and table if they don't already exit"""

        conn = db.raw_connection().cursor()
        conn.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{PGDATABASE}'")
        exists = conn.fetchone()
        if not exists:
            db.execution_options(isolation_level="AUTOCOMMIT").execute(f"CREATE DATABASE {PGDATABASE}")
        cli_db = create_engine(config.PG_DB_URL)
        if not inspect(cli_db).has_table(PG_LOG_TABLE):
            metadata = MetaData(cli_db)
            # Create a table with the appropriate Columns
            Table(PG_LOG_TABLE, metadata,
                  Column('date', DateTime),
                  Column('name', String(100)),
                  Column('level', String(50)),
                  Column('message', Text),
                  )
            # Implement the creation
            metadata.create_all()
        return cli_db

    def run(self):
        self.flush_logs_to_db()
        return {"files": self.files}

    def flush_logs_to_db(self):
        """ Flush all generates logs to the database """
        log.info("Line before flushing")

        with open(LOG_FILE_PATH, "r") as log_file:
            cmd = f'COPY {config.PG_LOG_TABLE}(date, name, level, message) FROM STDIN WITH (FORMAT CSV, HEADER FALSE)'
            conn = self.db_conn.raw_connection()
            conn.cursor().copy_expert(cmd, log_file)
            conn.commit()

