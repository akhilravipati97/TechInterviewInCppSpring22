from tracemalloc import start
from typing import List
from datetime import datetime


class Contest:
    def __init__(self, contest_id: str, contest_start_dt: datetime = None, contest_end_dt: datetime = None) -> None:
        self.contest_id = contest_id
        self.contest_start_dt = contest_start_dt
        self.contest_end_dt = contest_end_dt