from datetime import datetime
from datetime import timedelta
from contest_platform.base import Grading, User, Contest
from constants import EST_TZINFO
from contest_platform.codeforces import Codeforces
from contest_platform.atcoder import Atcoder
from contest_platform.codechef import Codechef
from contest_platform.leetcode import Leetcode
from contest_platform.dmoj import Dmoj
from util.datetime import get_course_week
from util.log import get_logger
import traceback
from collections import defaultdict

LOG = get_logger("Grader")

# Main constants
# NOTE: Can't move to constants.py cuz circular dependency
PLATFORMS = [Leetcode()]

# Testing this for now
def main():
    gd = Grading(delta=timedelta(days=7))
    LOG.debug(f"Checking for week_num: {gd.week_num} with {gd.week_start_dt} to {gd.week_end_dt}")

    PLATFORM_CONTESTS = {platform: platform.all_contests(gd) for platform in PLATFORMS}
    
    usr = User("yincheng929") # User("yin929")
    point_map = defaultdict(int)
    for platform, contests in PLATFORM_CONTESTS.items():
        for ct in contests:
            try:
                point_map[platform.name()] += platform.successful_submissions(gd, ct, usr)
            except Exception as e:
                traceback.print_exc()
                LOG.error(f"Exception for {platform.name()} ^")

    LOG.info(f"[GRADER]: Points map for user: {usr.user_id} is: {point_map}")
    LOG.info(f"[GRADER]: Num points for user: {usr.user_id} is {sum(point_map.values())}")



if __name__ == "__main__":
    main()