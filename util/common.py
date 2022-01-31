from util.log import get_logger

LOG = get_logger("common")


# Log and raise exception
def fail(s: str, logger = LOG):
    logger.error(s)
    raise Exception(s)
