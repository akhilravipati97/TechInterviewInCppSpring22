from typing import List
from util.web import WebRequest
from util.log import get_logger
from platform.base import PlatformBase, Grading, User, Contest
from datetime import datetime, timedelta
import requests as r
from util.datetime import in_between_dt, to_dt
from constants import EST_TZINFO
from util.common import fail

LOG = get_logger("Atcoder")

# https://github.com/kenkoooo/AtCoderProblems/blob/master/doc/api.md

class Atcoder(PlatformBase):
    """
        Atcoder does not have an official API. Scraping is possible with login.

        However, there is a stable unofficial API available, so we'll be using that. 

        Source: https://github.com/kenkoooo/AtCoderProblems/blob/master/doc/api.md

        Rate-limiting of 1s per request will apply, to be respectful to the public api.
    """

    PLATFORM = "Atcoder"
    CONTESTS_URL = "https://kenkoooo.com/atcoder/resources/contests.json"
    SUBMISSIONS_URL = "https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions?user={user_id}&from_second={from_ts_sec}"
    WR = WebRequest(rate_limit_millis=1000)
    SUBMISSION_DATA_CACHE = dict()


    def name(self):
        return Atcoder.PLATFORM


    def all_contests(self, gd: Grading) -> List[Contest]:
        """
            Atcoder via kenkoooo provides all available contests and requires us to filter
            after reading the whole response.

            Return a list of contest ids.

            Sample json:
            [
                {
                    "id": "abc236",
                    "start_epoch_second": 1642939200,
                    "duration_second": 6000,
                    "title": "AtCoder Beginner Contest 236",
                    "rate_change": " ~ 1999"
                },
                ...
        """

        contests = Atcoder.WR.get(Atcoder.CONTESTS_URL)
        if (contests is None) or (len(contests) == 0):
            fail(f"No contests found", LOG)

        contests = [{**contest, "startDatetime": to_dt(int(contest["start_epoch_second"])*1000)} for contest in contests]
        contests = [contest for contest in contests if in_between_dt(contest["startDatetime"], gd.week_start_dt, gd.week_end_dt)]
        LOG.debug(f"Contests: {contests}")
        return [Contest(str(contest["id"])) for contest in contests]
        

    def successful_submissions(self, gd: Grading, ct: Contest, usr: User) -> int:
        """
            The API returns all submission by a user after a certain timestamp. We'll have to filter
            it separately by ourselves. 
            
            NOTE: We can also cache results internally to prevent repeated calls.

            Sample json:
            [
                {
                    "id": 28755620,
                    "epoch_second": 1642944724,
                    "problem_id": "abc236_d",
                    "contest_id": "abc236",
                    "user_id": "xssliosx",
                    "language": "C++ (GCC 9.2.1)",
                    "point": 0,
                    "length": 2114,
                    "result": "WA",
                    "execution_time": 2205
                },
                ...
        """
        from_ts_sec = int(gd.week_start_dt.timestamp())
        submissions_url = Atcoder.SUBMISSIONS_URL.format(user_id=usr.user_id, from_ts_sec=from_ts_sec)
        LOG.debug(f"Submission url: {submissions_url}")

        if submissions_url in Atcoder.SUBMISSION_DATA_CACHE:
            LOG.debug(f"Submissions found in Cache with url: {submissions_url}")
            submissions = Atcoder.SUBMISSION_DATA_CACHE[submissions_url]
        else:
            submissions = Atcoder.WR.get(submissions_url)
            #LOG.debug(f"Submissions request response: {submissions}")
        Atcoder.SUBMISSION_DATA_CACHE[submissions_url] = submissions

        solved_questions = set()
        for submission in submissions:
                if submission["result"] == "AC" and submission["contest_id"] == ct.contest_id:
                    solved_questions.add(submission["problem_id"])

        LOG.debug(f"User [{usr.user_id}] in contest [{ct.contest_id}] solved these questions: [{solved_questions}]")
        return len(solved_questions)