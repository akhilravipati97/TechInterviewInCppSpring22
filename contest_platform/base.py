from datetime import datetime, timedelta
from typing import List
from util.datetime import get_course_week
from constants import EST_TZINFO

class Grading:
    def __init__(self, delta: timedelta()) -> None:
        self.grading_dt = datetime.now(EST_TZINFO) - delta
        self.week_start_dt, self.week_end_dt, self.week_num = get_course_week(self.grading_dt)

class Contest:
    def __init__(self, contest_id: str) -> None:
        self.contest_id = contest_id

class User:
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id

class PlatformBase:
    def name() -> str:
        raise Exception("Unimplemented name")

    def all_contests(self, gd: Grading) -> List[Contest]:
        raise Exception("Unimplemented get_contests")

    def successful_submissions(self, gd: Grading, ct: Contest, usr: User) -> int:
        raise Exception("Unimplemented successful_submissions")