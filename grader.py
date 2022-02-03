from datetime import datetime
from datetime import timedelta
from contest_platform.base import Grading, User, Contest
from constants import EST_TZINFO
from contest_platform.codeforces import Codeforces
from contest_platform.atcoder import Atcoder
from contest_platform.codechef import Codechef
from contest_platform.leetcode import Leetcode
from contest_platform.dmoj import Dmoj
from practice_platform.uva import Uva
from practice_platform.spoj import Spoj
from util.datetime import get_course_week
from util.log import get_logger
import traceback
from collections import defaultdict

LOG = get_logger("Grader")

# Main constants
# NOTE: Can't move to constants.py cuz circular dependency
CONTEST_PLATFORMS = [Dmoj()]
PRACTICE_PLATFORMS = [Spoj()]

# Testing this for now
def main():
    gd = Grading(delta=timedelta(days=7))
    LOG.debug(f"Checking for week_num: {gd.week_num} with {gd.week_start_dt} to {gd.week_end_dt}")

    PLATFORM_CONTESTS_MAP = {platform: platform.all_contests(gd) for platform in CONTEST_PLATFORMS}
    
    usr = User("lord_sahu") # User("yin929")
    point_map = defaultdict(int)
    for platform, contests in PLATFORM_CONTESTS_MAP.items():
        for ct in contests:
            try:
                point_map[platform.name()] += platform.successful_submissions(gd, ct, usr)
            except Exception as e:
                traceback.print_exc()
                LOG.error(f"Exception for {platform.name()} ^")

    LOG.info(f"[GRADER]: Points map for user: {usr.user_id} is: {point_map}")
    LOG.info(f"[GRADER]: Num points for user: {usr.user_id} is {sum(point_map.values())}")


    for platform in PRACTICE_PLATFORMS:
        try:
            point_map[platform.name()] += platform.successfull_submissions(gd, usr)
        except Exception as e:
            traceback.print_exc()
            LOG.error(f"Exception for {platform.name()} ^")

    LOG.info(f"[GRADER]: Points map for user: {usr.user_id} is: {point_map}")
    LOG.info(f"[GRADER]: Num points for user: {usr.user_id} is {sum(point_map.values())}")




if __name__ == "__main__":
    main()