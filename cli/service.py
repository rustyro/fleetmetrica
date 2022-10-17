import json
from datetime import datetime, timedelta
import argparse
import sys
import pandas as pd
import random
from config import db, PGDATABASE, LOG_FILE_PATH, PG_LOG_TABLE, IS_LAMBDA
import config
from .logging import Logger as Logr, log
from sqlalchemy import Table, Column, DateTime, String, MetaData, Text, inspect, create_engine
from typing import List
from functools import partial
import re
from dataclasses import dataclass
import os
from dateutil import parser as psr
from pathlib import Path


sys.stdout = Logr(LOG_FILE_PATH)
parser = argparse.ArgumentParser(
    description='Generate mock trucking data')
parser.add_argument('-f', '--files', nargs='+', help='path to sample files used for generation')
parser.add_argument('-dr', '--date_range', help='Date range for the mock dataset (MM-DD-YY:MM-DD-YY)')
parser.add_argument('-ds', '--data_size', default=0, type=int, help='Number of records to generate in the dataset')
parser.add_argument('-s', '--store', default="./mocks", type=str, help='Storage location for the generate files')
parser.add_argument('-c', '--config', help='Datasource configuration type')
parser.add_argument('-po', '--pattern_options', help='Pattern options')


def ts():
    return int(datetime.now().timestamp() * 1000)


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
    config = 'performance1'
    date_range = None


class MetricObject(object):
    """
    An object instance of any entity that can be mocked
    """

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

    def gen(self, size: int, conf: dict, parent_mocks: list = None):
        """
        Generate additional mock entries based on the object instance
        :param size: Number of records to generate from the object instance
        :param conf: configuration details on how to populate values of the instance attributes
        :param parent_mocks: Array of previously generated mocks that have a bearing on some values of the instance
        :return:
        """
        last_row = self.last_row
        curr_row = {}
        rows = []
        for i in range(size):
            row = self.gen_row(conf)
            rows.append(row)
        df = pd.DataFrame.from_dict(rows)

        return df

    def gen_row(self, conf: dict = None):
        curr_row = {}
        conf = conf or self.conf
        for key, conf in conf.get("properties").items():
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
        """Set the current value to the value of another parameter of the instance either previous or current"""
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
        start = end - timedelta(days=7)
        self.files = getattr(args, "files", None)
        self.date_range = getattr(args, "date_range", None) or f"{start.strftime('%m-%d-%y')}:{end.strftime('%m-%d-%y')}"
        self.data_size = getattr(args, "data_size", 2000) or 2000
        self.records_left = getattr(args, "data_size", 2000) or 2000
        self.store = getattr(args, "store", "./mocks")
        self.store_name = self.store
        self.store = f"/tmp/{self.store}" if IS_LAMBDA else self.store
        self.configs = self.load_configs()
        self.source_config = getattr(args, "config", None)
        self.pattern_options = getattr(args, "pattern_options", "")
        try:
            self.db_conn = self.init_db()
        except:
            log.warning("could not make database connection. Logs will not be save to DB")
            self.db_conn = None
        self.drivers = None

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

    def get_drivers(self, driver_df):
        drivers = [MetricObject(row.to_dict(), {}) for i, row in driver_df.iterrows()]
        self.drivers = drivers

    def get_daterange(self):
        """get the dates within the date range"""
        splitted = self.date_range.split(":")
        try:
            start = psr.parse(splitted[0])
            end = psr.parse(splitted[1])
        except:
            msg = "unable to parse date range, please use format: mm-dd-yy:mm:dd:yy"
            log.error(msg)
            raise Exception(msg)
        # print(start, end)
        if start > end:
            msg = "Start date cannot be greater than end date"
            log.error(msg)
            raise Exception(msg)
        diff_days = end - start
        if diff_days.days > 30:
            raise Exception("Max number of days exceeded. Enter a range <= 30 days")
        dates = [start + timedelta(days=i) for i in range(diff_days.days) if diff_days]
        dates = dates if dates else [start]
        return dates

    def get_number_of_records(self):
        num = random.randint(1, 50)
        if num > self.records_left:
            num = self.records_left
        return max([1, num])

    def run(self):
        fconfig = self.configs.get(self.source_config)

        if not fconfig:
            log.error(f"Cannot process {self.files}. Invalid or no configuration specified. Aborting...")
            return

        files_and_config = {}
        nof = fconfig.get("no_of_files", 1)
        for f in self.files:
            splitted = f.split(":")
            if not len(splitted) == nof:
                log.warning(f"Cannot process {f}. Invalid file pattern. Aborting...")
                return

            filepath = splitted[0]
            fileconfig = splitted[1] if nof > 1 else self.source_config
            try:
                df = pd.read_csv(filepath)
            except Exception as e:
                log.warning(f"could not load {filepath}, bad input file.")
                return

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
            files_and_config[fileconfig] = {"filepath": filepath, "dataframe": drivers}

            # load drivers
            if fconfig.get("driver_file_tag") == fileconfig:
                self.get_drivers(drivers)

        for date in self.get_daterange():

            for order in fconfig.get("execution_order", []):
                mock_df = pd.DataFrame(columns=list(fconfig.get("properties", {}).keys()))

                try:
                    for driver in self.drivers:
                        mock_conf = self.configs.get(order)
                        parent_mocks = None
                        if depends_on := mock_conf.get("depends_on", None):
                            parent_mocks = {k: v for k, v in files_and_config.items() if k in depends_on}
                        size = self.get_number_of_records()
                        self.records_left -= size
                        mo_df = driver.gen(size, mock_conf, parent_mocks)
                        mock_df = pd.concat([mock_df, mo_df])
                except Exception as e:
                    log.warning(f"skipped generation of {order}, error: {e}")
                    continue

                # reset records left
                self.records_left = self.data_size
                sort_by = fconfig.get("sort_by", fconfig.get("identifier"))
                mock_df = mock_df.sort_values(sort_by)
                files_and_config[order]["mocked_df"] = mock_df
                # export to csv
                fp = files_and_config.get(order).get("filepath")
                fname = fp.split('/')[-1]
                store_path = f"{self.store}/{str(date.date())}"
                Path(store_path).mkdir(parents=True, exist_ok=True)
                mock_df.to_csv(f"{store_path}/{order}.csv", index=False)

        return self

    def flush_logs_to_db(self):
        """ Flush all generates logs to the database """
        log.info("Cleaning up")
        if not self.db_conn:
            return
        with open(LOG_FILE_PATH, "r") as log_file:
            cmd = f'COPY {config.PG_LOG_TABLE}(date, name, level, message) FROM STDIN WITH (FORMAT CSV, HEADER FALSE)'
            conn = self.db_conn.raw_connection()
            conn.cursor().copy_expert(cmd, log_file)
            conn.commit()
