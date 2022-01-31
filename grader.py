from datetime import datetime
from datetime import timedelta
from constants import EST_TZINFO
from platform.codeforces import Codeforces
from util.datetime import get_course_week
from util.log import get_logger
import traceback
from collections import defaultdict

LOG = get_logger("Grader")

# Main constants
# NOTE: Can't move to constants.py cuz circular dependency
PLATFORMS = [Codeforces()]

# Testing this for now
def main():
    dt = datetime.now(EST_TZINFO) - timedelta(days=7)
    start_dt, end_dt, week_num = get_course_week(dt)
    LOG.debug(f"Checking for week_num: {week_num} with {start_dt} to {end_dt}")

    PLATFORM_CONTESTS = {platform: platform.all_contests(start_dt, end_dt) for platform in PLATFORMS}
    
    user_id = "yin929"
    point_map = defaultdict(int)
    for platform, contests in PLATFORM_CONTESTS.items():
        for contest_id in contests:
            try:
                point_map[platform.name()] += platform.successful_submissions(contest_id, user_id)
            except Exception as e:
                traceback.print_exc(e)
                LOG.error(f"Exception for {platform.name()} ^")

    LOG.info(f"[GRADER]: Points map for user: {user_id} is: {point_map}")
    LOG.info(f"[GRADER]: Num points for user: {user_id} is {sum(point_map.values())}")



if __name__ == "__main__":
    main()