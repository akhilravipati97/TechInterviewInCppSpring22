from datetime import datetime, timedelta
from constants import EST_TZINFO
from util.datetime import get_course_week

class Grading:
    def __init__(self, delta: timedelta()) -> None:
        self.grading_dt = datetime.now(EST_TZINFO) - delta
        self.week_start_dt, self.week_end_dt, self.week_num = get_course_week(self.grading_dt)
