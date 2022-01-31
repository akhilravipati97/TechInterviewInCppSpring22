import logging_init
from platform_base import PlatformBase
from datetime import datetime
import requests as r

class Codeforces(PlatformBase):
    CONTESTS_URL = "https://codeforces.com/api/contest.list"


    def all_contests(self, start_date: datetime, end_date: datetime):
        contests = r.get(Codeforces.CONTESTS_URL).json()
        if contests is None:
            return []
        

    def successful_submissions(self, contest: str, user_id: str):
        raise Exception("Unimplemented successful_submissions") 