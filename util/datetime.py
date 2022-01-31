from TechInterviewInCppSpring22.constants import TIC_WEEK_1_START_DATE
import logging_init
from datetime import datetime, timedelta
from typing import Tuple
import pytz
from constants import TIC_WEEK_START_DATES
from util.common import fail

EST_TZINFO = pytz.timezone("America/New_York")
EST_DATE = datetime.now(EST_TZINFO)
EST_TZINFO_DELTA = EST_DATE.tzinfo.utcoffset(EST_DATE)

LOG = logging_init.tic_logger

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
    