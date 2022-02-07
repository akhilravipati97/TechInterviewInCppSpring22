from practice_platform.base import PracticePlatformBase
from model.user import User
from model.grading import Grading
from model.contest import Contest
from typing import Dict, List, Set
from collections import defaultdict

class TopcoderPractice(PracticePlatformBase):
    def name() -> str:
        raise Exception("Unimplemented name")

    def successfull_submissions(self, gd: Grading, usr: User, usr_cts_sq: Dict[str, Set[str]] = defaultdict(set)) -> int:
        raise Exception("Unimplemented successful_submissions")