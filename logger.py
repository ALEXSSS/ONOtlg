import logging
import sys
import time
from logging.handlers import RotatingFileHandler

from PROPERTY import PROD

LOG = logging.basicConfig(filename='log.log', level=logging.INFO)
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

formatter = logging.Formatter('%(asctime)s : %(message)s', '%b %d %H:%M:%S')
formatter.converter = time.gmtime

logger = logging.getLogger("Rotating Log")
file_handler = RotatingFileHandler('log.log', maxBytes=20 * (2 ** 10), backupCount=2)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

if PROD:
    logger.addHandler(file_handler)
else:
    logger.addHandler(console_handler)


# If you want to set the logging level from a command-line option such as:
# --log=INFO

def log(messages, *addition):
    logger.info(messages + "\n ".join(addition))
    # print(label, message)
