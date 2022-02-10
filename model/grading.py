from calendar import week
from datetime import datetime, timedelta
from util.log import get_logger
from constants import EST_TZINFO
from util.datetime import get_course_week, get_course_week_by_num
from util.common import fail

LOG = get_logger("Grading")

class Grading:
    """
    Initialize the grading week start, end date based on week number or time delta from current date.
    
    Week nums and start dates are generated from here: TIC_WEEK_START_DATES in contants.py

    But as of now, Week nums are 1-indexed starting from datetime(2022, 1, 15, tzinfo=EST_TZINFO)

    """
    def __init__(self, delta: timedelta = None, week_num: int = None) -> None:
        LOG.debug(f"[delta, week_num]: [{delta}, {week_num}]")
        if None not in [delta, week_num]:
            fail(f"Can only provide one of week_num or delta, provided both delta: [{delta}], week_num: [{week_num}]", LOG)

        self.grading_dt = datetime.now(EST_TZINFO)
        if (delta is None) and (week_num is None):
            self.week_start_dt, self.week_end_dt, self.week_num = get_course_week(self.grading_dt)
        elif delta is not None:
            self.grading_dt += delta
            self.week_start_dt, self.week_end_dt, self.week_num = get_course_week(self.grading_dt)
        elif week_num is not None:
            self.week_start_dt, self.week_end_dt, self.week_num = get_course_week_by_num(week_num)
        else:
            fail(f"Unknown branch of execution", LOG)
