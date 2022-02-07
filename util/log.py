import logging
import colorlog
import datetime
import os 
from constants import LOG_MODE_DEBUG, PROJECT_PATH

# Source: https://gist.github.com/aldur/f356f245014523330a7070ab12bcfb1f
# Configure logging.
# `export DEBUG=1` to see debug output.
# `mkdir logs` to write to files too.
# User common.get_logger to get a logger

LOGGING_INIT_PACKAGE_TIMESTAMP = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')

STREAM_FORMATTER = colorlog.ColoredFormatter(
    '%(log_color)s[%(asctime)s][%(levelname)-6s]%(cyan)s[%(name)-10s] - %(white)s%(message)s',
    "%H:%M:%S",
    log_colors={
        'DEBUG': 'blue',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
        'EXCEPTION': 'bold_red',
    })
#     STREAM_FORMATTER = logging.Formatter('%(levelname)s %(name)s %(message)s')


CONSOLE_HANDLER = logging.StreamHandler()
CONSOLE_HANDLER.setLevel(logging.DEBUG)
CONSOLE_HANDLER.setFormatter(STREAM_FORMATTER)


FILE_HANDLER = None

def __setup_file_handler(debug=False):
    global FILE_HANDLER
    if FILE_HANDLER is None:
        FILE_HANDLER = logging.FileHandler(os.path.join('logs', '{}_{}.log'.format(__name__, LOGGING_INIT_PACKAGE_TIMESTAMP)), mode='a')
        FILE_HANDLER.setLevel(logging.DEBUG if debug else logging.INFO)
        FILE_HANDLER.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)-6s][%(name)-10s] - %(message)s'))


def get_logger(name: str, debug = False) -> logging.Logger:
    debug = debug or LOG_MODE_DEBUG or os.environ.get('DEBUG')
    logger = logging.getLogger(name)

    if PROJECT_PATH.joinpath("logs").exists():
        __setup_file_handler(debug)
        logger.addHandler(FILE_HANDLER)
        
    logger.addHandler(CONSOLE_HANDLER)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    return logger