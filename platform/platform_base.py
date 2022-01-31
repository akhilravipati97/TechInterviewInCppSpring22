from datetime import datetime

class PlatformBase:
    def all_contests(self, start_date: datetime, end_date: datetime):
        raise Exception("Unimplemented get_contests")

    def successful_submissions(self, contest: str, user_id: str):
        raise Exception("Unimplemented successful_submissions")