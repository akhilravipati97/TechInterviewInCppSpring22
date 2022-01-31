from typing import List
from util.datetime import in_between_ts
from util.log import get_logger
from platform.platform_base import PlatformBase
from datetime import datetime
import requests as r
from util.datetime import in_between_dt, to_dt
from constants import EST_TZINFO
from util.common import fail

LOG = get_logger("Codeforces")

class Codeforces(PlatformBase):
    PLATFORM = "Codeforces"
    CONTESTS_URL = "https://codeforces.com/api/contest.list"
    SUBMISSIONS_URL = "https://codeforces.com/api/contest.status?contestId={contest_id}&handle={user_id}"


    def name(self):
        return Codeforces.PLATFORM


    def all_contests(self, start_dt: datetime, end_dt: datetime) -> List[str]:
        """
            Codeforces provides all available contests and requires us to filter
            after reading the whole response.

            Return a list of contest ids.

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
                ...
                ...
        """

        contests = r.get(Codeforces.CONTESTS_URL).json()
        if (contests is None) or ("result" not in contests):
            LOG.warn(f"[{Codeforces.PLATFORM}]: No contests found")
            return []

        contests = contests["result"]
        contests = [{**contest, "startDatetime": to_dt(int(contest["startTimeSeconds"])*1000)} for contest in contests]
        contests = [contest for contest in contests if in_between_dt(contest["startDatetime"], start_dt, end_dt)]
        LOG.debug(f"[{Codeforces.PLATFORM}]: Contests: {contests}")
        return [str(contest["id"]) for contest in contests]
        

    def successful_submissions(self, contest_id: str, user_id: str):
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

        submissions_url = Codeforces.SUBMISSIONS_URL.format(contest_id=contest_id, user_id=user_id)
        LOG.debug(f"[{Codeforces.PLATFORM}]: Submission url: {submissions_url}")

        submissions = r.get(submissions_url).json()
        LOG.debug(f"[{Codeforces.PLATFORM}]: Submissions request response: {submissions}")

        if submissions["status"] != "OK":
            LOG.error(f"[{Codeforces.PLATFORM}]: Unsuccessful submissions request. response: {submissions}")
            fail(f"[{Codeforces.PLATFORM}]: Submissions not found for [{user_id}] in [{contest_id}].")

        solved_questions = set()
        for submission in submissions["result"]:
            if submission["verdict"] == "OK":
                solved_questions.add(submission["problem"]["name"] + " -- " + submission["problem"]["index"] )

        LOG.debug(f"[{Codeforces.PLATFORM}]: User [{user_id}] in contest [{contest_id}] solved these questions: [{solved_questions}]")
        return len(solved_questions)
