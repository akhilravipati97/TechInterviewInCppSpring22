from datetime import datetime
from typing import List

class PlatformBase:
    def name() -> str:
        raise Exception("Unimplemented name")

    def all_contests(self, start_date: datetime, end_date: datetime) -> List[str]:
        raise Exception("Unimplemented get_contests")

    def successful_submissions(self, contest: str, user_id: str) -> int:
        raise Exception("Unimplemented successful_submissions")