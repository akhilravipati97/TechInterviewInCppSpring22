from collections import defaultdict
from typing import Dict, List, Set
from model.submission import Submission
from util.web import WebRequest
from util.log import get_logger
from contest_platform.base import ContestPlatformBase, Grading, User, Contest
from datetime import datetime, timedelta
import requests as r
from util.datetime import in_between_dt, to_dt_from_ts
from constants import EST_TZINFO
from util.common import fail

LOG = get_logger("AtcoderPractice")

# https://github.com/kenkoooo/AtCoderProblems/blob/master/doc/api.md

class AtcoderPractice(ContestPlatformBase):
    """
        Atcoder does not have an official API. Scraping is possible with login.

        However, there is a stable unofficial API available, so we'll be using that. 

        Source: https://github.com/kenkoooo/AtCoderProblems/blob/master/doc/api.md

        Rate-limiting of 1s per request will apply, to be respectful to the public api.
    """

    PLATFORM = "Atcoder"
    SUBMISSIONS_URL = "https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions?user={user_id}&from_second={from_ts_sec}"
    WR = WebRequest(rate_limit_millis=1000)


    def name(self):
        return AtcoderPractice.PLATFORM
        

    def successfull_submissions(self, gd: Grading, usr: User, usr_cts_sq: Dict[str, Set[str]] = defaultdict(set)) -> int:
        """
            The API returns all submission by a user after a certain timestamp. We'll have to filter
            it separately by ourselves. 

            NOTE: This is exactly similar to Atcoder contests class's successfull_submissions method. The difference is that we 
            remove the contest time filter. i.e accept all submissions made to a contest within the grading week irrespective of
            when they were made. We'll remove those submissions that were made during the contest based on usr_cts_sq.
        """
        usr_handle = usr.handle(self.name())
        from_ts_sec = int(gd.week_start_dt.timestamp())
        submissions_url = AtcoderPractice.SUBMISSIONS_URL.format(user_id=usr_handle, from_ts_sec=from_ts_sec)
        LOG.debug(f"Submission url: {submissions_url}")

        submissions = AtcoderPractice.WR.get(submissions_url)

        all_contest_problems = defaultdict(set)
        for submission in submissions:
            curr_dt = to_dt_from_ts(int(submission["epoch_second"])*1000)
            if submission["result"] == "AC" and in_between_dt(curr_dt, gd.week_start_dt, gd.week_end_dt):
                all_contest_problems[submission["contest_id"]].add(submission["problem_id"])

        contest_practice_problems = dict()
        for contest_id, problems in all_contest_problems.items():
            if contest_id in usr_cts_sq:
                separate_problems = problems - usr_cts_sq[contest_id]
                LOG.debug(f"User: [{usr_handle}] already participared in contest: [{contest_id}]. Unsolved, i.e num practice problems are: [{len(separate_problems)}] which are: [{separate_problems}]")
                contest_practice_problems[contest_id] = separate_problems
            else:
                contest_practice_problems[contest_id] = problems
            
        num_practice_problems = sum([len(problems) for problems in contest_practice_problems.values()])
        LOG.debug(f"User: [{usr_handle}] has solved: [{num_practice_problems}] questions: [{contest_practice_problems}]")
        return num_practice_problems