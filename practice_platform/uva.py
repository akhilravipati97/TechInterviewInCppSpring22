from collections import defaultdict
from distutils.log import debug
from re import sub
from typing import Dict, List, Set
from webbrowser import get
from util.datetime import to_dt_from_ts
from model.user import User
from model.grading import Grading
from model.contest import Contest
from practice_platform.base import PracticePlatformBase
from util.web import WebRequest
from util.common import fail
from util.log import get_logger
from util.datetime import in_between_dt

LOG = get_logger("Uva")


class UvaPractice(PracticePlatformBase):
    """
    Uva has a well documented API, which is what we'll be using.

    Source: https://uhunt.onlinejudge.org/api
    """

    PLATFORM = "Uva"

    USERID_TO_UID_URL = "https://uhunt.onlinejudge.org/api/uname2uid/{user_id}"

    # NOTE: This allows for options to limit the number of submissions or filter based on minimum submission id. 
    # The latter looks promising, but it would carrying state across grading weeks. For now, all submissions are fetched.
    SUBMISSIONS_URL = "https://uhunt.onlinejudge.org/api/subs-user/{uid}"

    WR = WebRequest(rate_limit_millis=1000)

    def name(self) -> str:
        return UvaPractice.PLATFORM

    
    def __get_uid(self, usr: User) -> str:
        usr_handle = usr.handle(self.name())
        uid_url = UvaPractice.USERID_TO_UID_URL.format(user_id=usr_handle)
        LOG.debug(f"Fecthing uid for user: [{usr_handle}] at: [{uid_url}]")

        return str(UvaPractice.WR.get(uid_url, is_json=True))


    def successfull_submissions(self, gd: Grading, usr: User, usr_cts_sq: Dict[str, Set[str]] = defaultdict(set)) -> int:
        """
        Uva API works with numeric uid. For that, Uva user id has to be converted to uid.
        """
        usr_handle = usr.handle(self.name())
        uid = self.__get_uid(usr)
        submissions_url = UvaPractice.SUBMISSIONS_URL.format(uid=uid)
        LOG.debug(f"Submissions url: [{submissions_url}]")
        
        submissions = UvaPractice.WR.get(submissions_url)
        if (submissions is None) or ("subs" not in submissions):
            fail(f"No submissions found for user: [{usr_handle}] at [{uid}]", LOG)
        
        if len(submissions["subs"]) == 0:
            return 0

        # NOTE: We could take advantage of the ordering, but if we choose to pursue other alternative to 
        # reduce the number of submissions returned in the first place, we may not need this. So, for now,
        # we'll ignore the ordering and process the full list.
        submissions = submissions["subs"]

        problem_ids = set()
        for submission in submissions:
            problem_id = int(submission[1])
            verdict = int(submission[2])
            submission_dt = to_dt_from_ts(int(submission[4])*1000)
            if verdict == 90 and in_between_dt(submission_dt, gd.week_start_dt, gd.week_end_dt):
                problem_ids.add(problem_id)
        
        LOG.debug(f"User: [{usr_handle}] has solved: [{len(problem_ids)}] questions: [{problem_ids}]")
        return len(problem_ids)