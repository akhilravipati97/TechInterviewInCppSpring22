from model.user import User
from model.grading import Grading

class PracticePlatformBase:
    def name() -> str:
        raise Exception("Unimplemented name")

    def successfull_submissions(self, gd: Grading, usr: User) -> int:
        raise Exception("Unimplemented successful_submissions")