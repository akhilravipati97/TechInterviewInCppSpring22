from typing import Dict, List, Set
from util.datetime import to_dt_from_ts
from model.user import User
from model.grading import Grading
from model.contest import Contest
from practice_platform.base import PracticePlatformBase
from util.web import WebRequest
from util.common import fail
from util.log import get_logger
from util.datetime import in_between_dt
from collections import defaultdict

LOG = get_logger("CodeforcesPractice")


class CodeforcesPractice(PracticePlatformBase):
    """
    Codeforces has a well documented API, which is what we'll be using.

    Source: https://codeforces.com/apiHelp/methods
    """

    PLATFORM = "Codeforces"

    # from_count is 1 indexed
    # submission_count is the number of submission to show at once
    SUBMISSIONS_URL = "https://codeforces.com/api/user.status?handle={user_id}&from={from_count}&count={submission_count}"
    SUBMISSIONS_COUNT = 50
    START_FROM_COUNT = 1

    WR = WebRequest(rate_limit_millis=1000)

    def name(self) -> str:
        return CodeforcesPractice.PLATFORM


    def successfull_submissions(self, gd: Grading, usr: User, usr_cts_sq: Dict[str, Set[str]] = defaultdict(set)) -> int:
        """
        Generally problems belong to various contests. We don't want to double count problems.
        If a user solved it in a contest we do not want to add points for it again for problems.

        cts list is the list of contests that the user participated in and each of those contest
        objects will have the solved questions. We'll be using that to disambiguate and prevent
        double count.

        Sample json:
        {
            "status": "OK",
            "result": [
                {
                "id": 145083228,
                "contestId": 1091,
                "creationTimeSeconds": 1643938894,
                "relativeTimeSeconds": 2147483647,
                "problem": {
                    "contestId": 1091,
                    "index": "A",
                    "name": "New Year and the Christmas Ornament",
                    "type": "PROGRAMMING",
                    "points": 500,
                    "rating": 800,
                    "tags": []
                },
                "author": {...},
                "programmingLanguage": "GNU C11",
                "verdict": "OK",
                "testset": "TESTS",
                "passedTestCount": 42,
                "timeConsumedMillis": 15,
                "memoryConsumedBytes": 0
                },
                ...
        """

        short_circuit = False
        separately_solved_questions = defaultdict(set) # {contest => set(problem_id)]}
        curr_count = 1
        while not short_circuit:
            submissions_url = CodeforcesPractice.SUBMISSIONS_URL.format(user_id=usr.user_id, from_count=curr_count, submission_count=CodeforcesPractice.SUBMISSIONS_COUNT)
            LOG.debug(f"Submissions url: [{submissions_url}]")
            
            submissions = CodeforcesPractice.WR.get(submissions_url)
            if (submissions is None) or ("status" not in submissions) or (submissions["status"] != "OK"):
                fail(f"No submissions found for user: [{usr.user_id}] at [{submissions_url}]")

            if (len(submissions["result"]) == 0):
                short_circuit = True
                break

            # NOTE: Submissions are returned desc order of submission id, which normally changes linearly with submission time. So we can short-circuit
            # when one of the submission is past the limits
            submissions = submissions["result"]

            for submission in submissions:
                curr_dt = to_dt_from_ts(submission["creationTimeSeconds"]*1000)
                verdict = submission["verdict"]
                contest_id = str(submission["contestId"])
                problem_id = submission["problem"]["name"] + " -- " + submission["problem"]["index"]
                
                if in_between_dt(curr_dt, gd.week_start_dt, gd.week_end_dt) and verdict == "OK":
                    separately_solved_questions[contest_id].add(problem_id)

                if curr_dt < gd.week_start_dt:
                    LOG.debug(f"Curr dt: [{curr_dt}] is less than [{gd.week_start_dt}], so short circuiting.")
                    short_circuit = True
                    break

            curr_count += CodeforcesPractice.SUBMISSIONS_COUNT
        LOG.debug(f"Separately solved questions pre-filtering: [{separately_solved_questions}]")

        # Regular points
        REGULAR_POINTS = defaultdict(set)
        for contest_id, problems in separately_solved_questions.items():
            if contest_id in usr_cts_sq:
                separate_problems = problems - usr_cts_sq[contest_id]
                LOG.debug(f"User: [{usr.user_id}] already participared in contest: [{contest_id}]. Unsolved, i.e num practice problems are: [{len(separate_problems)}] which are: [{separate_problems}]")
                REGULAR_POINTS[contest_id] = separate_problems
            else:
                REGULAR_POINTS[contest_id] = problems
            
        num_practice_problems = sum([len(problems) for problems in REGULAR_POINTS.values()])
        LOG.debug(f"User: [{usr.user_id}] has solved: [{num_practice_problems}] questions: [{REGULAR_POINTS}]")
        return num_practice_problems