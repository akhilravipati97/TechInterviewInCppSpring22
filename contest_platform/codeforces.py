from typing import List
from util.web import WebRequest
from model.submission import Submission
from util.log import get_logger
from contest_platform.base import ContestPlatformBase, Grading, User, Contest
from datetime import datetime
import requests as r
from util.datetime import in_between_dt, to_dt_from_ts
from util.common import fail

LOG = get_logger("Codeforces")

class Codeforces(ContestPlatformBase):
    PLATFORM = "Codeforces"
    CONTESTS_URL = "https://codeforces.com/api/contest.list"
    SUBMISSIONS_URL = "https://codeforces.com/api/contest.status?contestId={contest_id}&handle={user_id}"
    WR = WebRequest(rate_limit_millis=1000)


    def name(self):
        return Codeforces.PLATFORM


    def all_contests(self, gd: Grading) -> List[Contest]:
        """
            Codeforces provides all available contests and requires us to filter
            after reading the whole response.

            Sample json:
            {
                "status": "OK",
                "result": [
                    {
                    "id": 1636,
                    "name": "Codeforces Round #TBA",
                    "type": "CF",
                    "phase": "BEFORE",
                    "frozen": false,
                    "durationSeconds": 8100,
                    "startTimeSeconds": 1645972500,
                    "relativeTimeSeconds": -2387738
                    },
                ...
        """

        contests = Codeforces.WR.get(Codeforces.CONTESTS_URL)
        if (contests is None) or ("result" not in contests):
            fail(f"No contests found", LOG)

        contests = contests["result"]
        contests = [{**contest, "startDatetime": to_dt_from_ts(int(contest["startTimeSeconds"])*1000)} for contest in contests]
        contests = [contest for contest in contests if in_between_dt(contest["startDatetime"], gd.week_start_dt, gd.week_end_dt)]
        LOG.debug(f"Contests: {contests}")
        return [Contest(str(contest["id"])) for contest in contests]
        

    def successful_submissions(self, gd: Grading, ct: Contest, usr: User) -> Submission:
        """
            Sample json:
            {
                "status": "OK",
                "result": [
                    {
                    "id": 144607357,
                    "contestId": 566,
                    "creationTimeSeconds": 1643597420,
                    "relativeTimeSeconds": 2147483647,
                    "problem": {
                        "contestId": 566,
                        "index": "C",
                        "name": "Logistical Questions",
                        "type": "PROGRAMMING",
                        "points": 3000,
                        "rating": 3000,
                        "tags": [
                        "dfs and similar",
                        "divide and conquer",
                        "trees"
                        ]
                    },
                    "author": {
                        "contestId": 566,
                        "members": [
                        {
                            "handle": "C202044zxy"
                        }
                        ],
                        "participantType": "PRACTICE",
                        "ghost": false,
                        "startTimeSeconds": 1438273200
                    },
                    "programmingLanguage": "GNU C++20 (64)",
                    "verdict": "OK",
                    "testset": "TESTS",
                    "passedTestCount": 43,
                    "timeConsumedMillis": 1138,
                    "memoryConsumedBytes": 36761600
                    },
        """

        submissions_url = Codeforces.SUBMISSIONS_URL.format(contest_id=ct.contest_id, user_id=usr.user_id)
        LOG.debug(f"Submission url: {submissions_url}")

        submissions = Codeforces.WR.get(submissions_url)
        #LOG.debug(f"Submissions request response: {submissions}")

        if submissions["status"] != "OK":
            LOG.error(f"Unsuccessful submissions request. response: {submissions}")
            fail(f"Submissions not found for [{usr.user_id}] in [{ct.contest_id}].", LOG)

        solved_questions = set()
        for submission in submissions["result"]:
            if submission["verdict"] == "OK":
                solved_questions.add(submission["problem"]["name"] + " -- " + submission["problem"]["index"] )

        LOG.debug(f"User [{usr.user_id}] in contest [{ct.contest_id}] solved these questions: [{solved_questions}]")
        return Submission(solved_questions)
