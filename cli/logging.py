import sys
import logging
from config import LOG_FILE_PATH
from datetime import datetime


open(LOG_FILE_PATH, "w+").close()

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
logging.basicConfig(filename=LOG_FILE_PATH,
                    filemode='a',
                    format='%(asctime)s.%(msecs)d, %(name)s, %(levelname)s, %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)

log = logging.getLogger("CLI")
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logFormatter)
log.addHandler(console_handler)


class Logger:

    def __init__(self, filename):
        self.console = sys.stdout
        try:
            self.file = open(filename, 'a')
        except OSError as e:
            filename = f"/tmp/{filename}"
            open(filename, "a").close()

    def write(self, message):
        if message not in ["", "\n", " "]:
            message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}, CLI, INFO, {str(message)}\n"
            self.console.write(message)
            self.file.write(message)
            self.file.flush()

    def flush(self):
        pass
