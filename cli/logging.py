import sys
import logging
from cli.config import LOG_FILE_PATH
from datetime import datetime

open(LOG_FILE_PATH, "w+").close()

logging.basicConfig(filename=LOG_FILE_PATH,
                    filemode='a',
                    format='%(asctime)s.%(msecs)d, %(name)s, %(levelname)s, %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)

log = logging.getLogger("CLI")


class Logger:

    def __init__(self, filename):
        self.console = sys.stdout
        self.file = open(filename, 'a')

    def write(self, message):
        if message not in ["", "\n", " "]:
            message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}, CLI, INFO, {str(message)}\n"
            self.console.write(message)
            self.file.write(message)
            self.file.flush()

    def flush(self):
        pass
