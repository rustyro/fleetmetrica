import json
from datetime import datetime, timedelta
import argparse
import sys
import pandas as pd
import random
from .config import db, PGDATABASE, LOG_FILE_PATH, PG_LOG_TABLE
from cli import config
from .logging import Logger as Logr, log
from sqlalchemy import Table, Column, Integer, DateTime, String, MetaData, Text, inspect, create_engine
from typing import List
from functools import partial
import re
from dataclasses import dataclass
import os


sys.stdout = Logr(LOG_FILE_PATH)
parser = argparse.ArgumentParser(
    description='Generate mock trucking data')
parser.add_argument('-f', '--files', nargs='+', help='path to sample files used for generation')
parser.add_argument('-dr', '--date_range', help='Date range for the mock dataset (DDMMYY-DDMMYY)')
parser.add_argument('-ds', '--data_size', default=0, help='Number of records to generate in the dataset')
parser.add_argument('-s', '--store', default=1, type=int, help='Storage location for the generate files')
parser.add_argument('-c', '--config', help='Datasource configuration type')
parser.add_argument('-po', '--patter_options', help='Pattern options')


def ts():
    return datetime.now().timestamp()


def dt():
    return datetime.now()


def randint():
    return random.randint(329419, 329513)


def add_to(val, range_: List[int] = None):
    range_ = range_ or [2, 12]
    num = random.randint(*range_)
    if isinstance(val, str) and re.match(r"(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})", val):
        ans = str(datetime.fromisoformat(val) + timedelta(hours=num))
    elif isinstance(val, (int, float)):
        ans = val + num
    else:
        ans = ""
    return ans


def randchoice(samples):
    return random.choice(samples)


funcs = {
    "func.timestamp": ts,
    "func.datetime": dt,
    "func.randint": randint,
    "func.add_to": partial(add_to),
    "func.randchoice": partial(randchoice),
}


samp = {'UNIQKEY': '1599748724376.317130.234', 'INSERT_DATETIME': '2020-09-10 11:38:44.369000000', 'STATUS': 0,
     'USERSTATUS': 0, 'PACKETID': 329464, 'LOGIN': '317130', 'DRIVERNAME': 'Robert Mason', 'VEHICLE_NUMBER': '23455',
     'STRT_DATIME': '2017-07-31 21:02:20', 'END_DATIME': '2020-09-10 11:28:34', 'LONG_IDLE_THRESH': 300,
     'RPM_THRESH': 2100, 'OVER_SPEED_THRESH': 65, 'XS_SPEED_THRESH': 80, 'STRT_ODOM': 502687.0, 'END_ODOM': 502687.0,
     'TRAVELED_MILES': 0.0}


@dataclass()
class Argz:
    files = ["./cli/fixtures/PERFORM_20200911.csv"]


with open('./cli/configs/performance.json') as pc:
    gen_conf = json.load(pc)


class MetricObject(object):
    """"""

    def __init__(self, data: dict, conf: dict):
        """"""
        self.conf = conf
        self.data = self.load_obj(data)
        self.curr_row = self.data.copy()
        self.last_row = self.data.copy()

    def load_obj(self, data: dict) -> dict:
        """load the object with the data properties"""
        for k, v in data.items():
            setattr(self, k, v)
        return data

    def gen(self, size):
        last_row = self.data.copy()
        curr_row = {}
        rows = []
        for i in range(size):
            row = self.gen_row()
            rows.append(row)
        df = pd.DataFrame.from_dict(rows)

        return df

    def gen_row(self):
        curr_row = {}
        for key, conf in self.conf.get("properties").items():
            generation = conf.get("generation", {})
            gen_func = getattr(self, generation.get("how", ""), None)
            val = gen_func(**generation.get("kwargs"))
            curr_row[key] = val
            self.curr_row = curr_row
        self.last_row = curr_row
        return curr_row

    def composite(self, src: str = None, keys: List[str] = None, **kwargs):
        src_ = self.last_row
        if src != "prev":
            src_ = self.curr_row
        vals = []
        for k in keys:
            if k.startswith("func"):
                vals.append(str(funcs.get(k)()))
            else:
                vals.append(str(src_.get(k)))
        return ".".join(vals)

    def direct(self, src: str = None, keys: List[str] = None, func: str = None, **kwargs):
        if src:
            src_ = self.last_row
            if src != "prev":
                src_ = self.curr_row
            vals = []
            for k in keys:
                vals.append(str(src_.get(k)))
            return "".join(vals)
        else:
            return funcs.get(func)(**kwargs.get("args", {}))

    def contiguous(self, src: str = None, follow: str = None, **kwargs):
        src_ = self.last_row
        if src != "prev":
            src_ = self.curr_row
        return src_.get(follow, "")

    def add_to(self, src: str = None, follow: str = None, **kwargs):
        src_ = self.last_row
        if src != "prev":
            src_ = self.curr_row
        res = funcs.get("func.add_to")(src_.get(follow, ""))
        return res

    def diff(self, src: str = None, keys: List[str] = None, **kwargs):
        src_ = self.last_row
        if src != "prev":
            src_ = self.curr_row
        high = float(src_.get(keys[0], 0))
        low = float(src_.get(keys[1], 0))
        return high - low


class CLI(object):

    def __init__(self, args: argparse.Namespace):
        end = datetime.now()
        start = end - timedelta(days=30)
        self.files = getattr(args, "files", None)
        self.date_range = getattr(args, "date_range", f"{start.strftime('%d%m%y')}-{end.strftime('%d%m%y')}")
        self.data_size = getattr(args, "data_size", 2000)
        self.store = getattr(args, "store", "./mock_data")
        self.configs = self.load_configs()
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

    @staticmethod
    def load_configs() -> dict:
        """Load specified configuration files to the CLI object"""
        directory = "./cli/configs"
        confs = {}
        for filename in os.listdir(directory):
            f = os.path.join(directory, filename)
            with open(f) as pc:
                confs[filename.split(".")[0]] = json.load(pc)
        return confs

    def run(self):
        # print("the files", self.files)
        # 1. load data from the sample files into memory based on the matching configs
        # gen_conf = None
        # with open('configs/perfomance.json') as pc:
        #     gen_conf = json.load(pc)
        for f in self.files:
            splitted = f.split(":")
            if not len(splitted) == 2:
                log.warning(f"Cannot process {f}, invalid file pattern. Aborting...")
                continue

            fp = splitted[0]
            fconfig = self.configs.get(splitted[1])

            if not fconfig:
                log.warning(f"Cannot process {f}, invalid configuration specified. Aborting...")

            try:
                df = pd.read_csv(fp)
            except Exception as e:
                log.warning(f"could not load {fp}, bad input file.")
                continue

            # drop comment rows
            comment_delimiter = fconfig.get("comment_delimiter", {})
            if comment_delimiter:
                comment_delimiter_idx = df.index[
                    df[comment_delimiter.get("column")] == comment_delimiter.get("delimiter")
                    ].to_list()
                if comment_delimiter_idx:
                    df = df.iloc[:comment_delimiter_idx[0]]

            # deduplicate the data
            drivers = df.drop_duplicates([fconfig.get("identifier")])

            mock_df = pd.DataFrame(columns=list(fconfig.get("properties", {}).keys()))
            for idx, row in drivers.iterrows():
                ""
                mo_df = MetricObject(row.to_dict(), fconfig).gen(5)
                mock_df = pd.concat([mock_df, mo_df])

            # export to csv
            fname = fp.split('/')[-1]
            mock_df.to_csv(f"./mocks/{fname}")

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

