from typing import List
from model.user import User
from model.contest import Contest
from model.grading import Grading
from model.submission import Submission


class ContestPlatformBase:
    def name() -> str:
        raise Exception("Unimplemented name")

    def pre_process(self, gd: Grading) -> None:
        raise Exception("Unimplemented pre_process")

    def all_contests(self, gd: Grading) -> List[Contest]:
        raise Exception("Unimplemented get_contests")

    def successful_submissions(self, gd: Grading, ct: Contest, usr: User) -> Submission:
        raise Exception("Unimplemented successful_submissions")