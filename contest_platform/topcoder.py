
from contest_platform.base import ContestPlatformBase
from typing import List
from model.user import User
from model.contest import Contest
from model.grading import Grading
from model.submission import Submission


class Topcoder(ContestPlatformBase):
    PLATFORM = "Topcoder"

    def name() -> str:
        return Topcoder.PLATFORM

    def all_contests(self, gd: Grading) -> List[Contest]:
        raise Exception("Unimplemented get_contests")

    def successful_submissions(self, gd: Grading, ct: Contest, usr: User) -> Submission:
        raise Exception("Unimplemented successful_submissions")