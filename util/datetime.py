from constants import TIC_WEEK_1_START_DATE
from util.log import get_logger
from datetime import datetime, timedelta
from typing import Tuple
import pytz
from constants import TIC_WEEK_START_DATES, EST_TZINFO_DELTA, EST_TZINFO
from util.common import fail


LOG = get_logger("util.datetime")

# https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive
def is_tz_aware(dt: datetime) -> bool:
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def is_est(dt: datetime) -> bool:
    return is_tz_aware(dt) and dt.tzinfo.utcoffset(dt) == EST_TZINFO_DELTA


# Ensure EST Date
def get_course_week(est_date: datetime) -> Tuple[datetime, datetime, int]:
    """
        Returns the current week's start time, end time (both inclusive), 
        and the week number as a tuple of 3 elements.
    """
    if not is_est(est_date):
        fail(f"Not an EST DATE: {est_date}")

    if est_date > TIC_WEEK_START_DATES[-1] or est_date < TIC_WEEK_1_START_DATE:
        fail(f"Date {est_date} not within the course duration: [{TIC_WEEK_1_START_DATE}, {TIC_WEEK_START_DATES[-1]}")

    for i, dt in enumerate(TIC_WEEK_START_DATES):
        if est_date < dt:
            return [TIC_WEEK_START_DATES[i-1], TIC_WEEK_START_DATES[i] - timedelta(seconds=1), i]


def to_dt_from_ts(epoch_millis: int) -> datetime:
    return datetime.fromtimestamp(epoch_millis/1000.0, tz=EST_TZINFO)

def to_dt_from_fmt(date_str: str, fmt: str) -> datetime:
    fail("Unimplemented to_dt_from_fmt")


def in_between_dt(target_dt: datetime, start_dt: datetime, end_dt: datetime) -> bool:
    """
        start_dt and end_dt inclusive.
    """
    return (target_dt >= start_dt) and (target_dt <= end_dt)

def in_between_ts(target_dt: datetime, start_epoch_ms: int, end_epoch_ms: int) -> bool:
    """
        start_epoch_ms, end_epoch_ms must both be milliseconds since unix epoch time,
        further the check is inclusive of both.
    """
    start_dt = datetime.fromtimestamp(start_epoch_ms/1000.0, tz=EST_TZINFO)
    end_dt = datetime.fromtimestamp(start_epoch_ms/1000.0, tz=EST_TZINFO)
    return in_between_dt(target_dt, start_dt, end_dt)


def get_curr_dt_est() -> datetime:
    return datetime.now(EST_TZINFO)
    