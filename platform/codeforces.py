import logging_init
from platform_base import PlatformBase
from datetime import datetime
import requests as r

LOG = logging_init.tic_logger

class Codeforces(PlatformBase):
    PLATFORM = "Codeforces"
    CONTESTS_URL = "https://codeforces.com/api/contest.list"


    def all_contests(self, start_date: datetime, end_date: datetime):
        contests = r.get(Codeforces.CONTESTS_URL).json()
        if (contests is None) or ("result" not in contests):
            LOG.warn(f"[{Codeforces.PLATFORM}]: No contests found")
            return []

        contests = contests["result"]
        contests = [contest for contest in contests if ]
        

    def successful_submissions(self, contest: str, user_id: str):
        raise Exception("Unimplemented successful_submissions") 