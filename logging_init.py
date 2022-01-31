import logging
import colorlog
import datetime
import os 

# Source: https://gist.github.com/aldur/f356f245014523330a7070ab12bcfb1f
# Configure logging.
# `export DEBUG=1` to see debug output.
# `mkdir logs` to write to files too.
# Create loggers with `import logging; logger = logging.getLogger(__name__)`

tic_logger = logging.getLogger("TIC")
tic_logger.setLevel(logging.INFO if not os.environ.get('DEBUG') else logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)


stream_formatter = colorlog.ColoredFormatter(
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
#     stream_formatter = logging.Formatter('%(levelname)s %(name)s %(message)s')

console_handler.setFormatter(stream_formatter)

package_timestamp = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
if os.path.isdir('logs'):
    file_handler = logging.FileHandler(
        os.path.join('logs', '{}_{}.log'.format(__name__, package_timestamp)), mode='a')
    file_handler.setLevel(logging.INFO if not os.environ.get('DEBUG') else logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
    tic_logger.addHandler(file_handler)

tic_logger.addHandler(console_handler)