import logging_init

LOG = logging_init.tic_logger

# Log and raise exception
def fail(s: str):
    LOG.error(s)
    raise Exception(s)
