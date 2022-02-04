from typing import List, Set


class Submission:
    def __init__(self, solved_questions: Set[str] = set()) -> None:
        self.solved_questions = solved_questions