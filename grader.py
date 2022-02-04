from datetime import datetime
from datetime import timedelta
from practice_platform.atcoder import AtcoderPractice
from contest_platform.base import Grading, User, Contest
from constants import EST_TZINFO, PRACTICE_PROBLEM_MULTIPLIER, CONTEST_PROBLEM_MULTIPLIER
from contest_platform.codeforces import Codeforces
from contest_platform.atcoder import Atcoder
from contest_platform.codechef import Codechef
from contest_platform.leetcode import Leetcode
from contest_platform.dmoj import Dmoj
from practice_platform.uva import UvaPractice
from practice_platform.spoj import SpojPractice
from practice_platform.codeforces import CodeforcesPractice
from util.datetime import get_course_week
from util.log import get_logger
import traceback
from collections import defaultdict

LOG = get_logger("Grader")

# Main constants
# NOTE: Can't move to constants.py cuz circular dependency
CONTEST_PLATFORMS = [Atcoder()]
PRACTICE_PLATFORMS = [AtcoderPractice()]

# Testing this for now
def main():
    #gd = Grading(delta=timedelta(days=7))
    gd = Grading()
    LOG.debug(f"Checking for week_num: {gd.week_num} with {gd.week_start_dt} to {gd.week_end_dt}")

    PLATFORM_CONTESTS_MAP = {platform: platform.all_contests(gd) for platform in CONTEST_PLATFORMS}
    USER_CONTEST_SUBMISSIONS_MAP = defaultdict(dict)
    
    usr = User("pescapescatarian") #User("canhnam357") # User("yin929")
    point_map = defaultdict(int)
    for platform, contests in PLATFORM_CONTESTS_MAP.items():
        for ct in contests:
            try:
                submissions = platform.successful_submissions(gd, ct, usr)
                USER_CONTEST_SUBMISSIONS_MAP[usr.user_id][ct.contest_id] = submissions.solved_questions
                point_map[platform.name()] += (CONTEST_PROBLEM_MULTIPLIER * len(submissions.solved_questions))
            except Exception as e:
                traceback.print_exc()
                LOG.error(f"Exception for {platform.name()} ^")

    LOG.info(f"[GRADER]: Points map for user: {usr.user_id} is: {point_map}")
    LOG.info(f"[GRADER]: Num points for user: {usr.user_id} is {sum(point_map.values())}")


    for platform in PRACTICE_PLATFORMS:
        try:
            user_contest_solved_questions = USER_CONTEST_SUBMISSIONS_MAP[usr.user_id]
            LOG.debug(f"Obtained [{user_contest_solved_questions}] for platform: [{platform.name()}]")
            point_map[platform.name()] += (PRACTICE_PROBLEM_MULTIPLIER * platform.successfull_submissions(gd, usr, user_contest_solved_questions))
        except Exception as e:
            traceback.print_exc()
            LOG.error(f"Exception for {platform.name()} ^")

    LOG.info(f"[GRADER]: Points map for user: {usr.user_id} is: {point_map}")
    LOG.info(f"[GRADER]: Num points for user: {usr.user_id} is {sum(point_map.values())}")




if __name__ == "__main__":
    main()