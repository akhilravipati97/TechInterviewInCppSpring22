import argparse
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Set
from contest_platform.base import ContestPlatformBase
from practice_platform.base import PracticePlatformBase
from util.datetime import get_curr_dt_est
from practice_platform.topcoder import TopcoderPractice
from contest_platform.topcoder import Topcoder
from practice_platform.atcoder import AtcoderPractice
from contest_platform.base import Grading, User, Contest
from constants import PRACTICE_PROBLEM_MULTIPLIER, CONTEST_PROBLEM_MULTIPLIER, CACHE_PATH
from contest_platform.codeforces import Codeforces
from contest_platform.atcoder import Atcoder
from contest_platform.codechef import Codechef
from contest_platform.leetcode import Leetcode
from contest_platform.dmoj import Dmoj
from practice_platform.uva import UvaPractice
from practice_platform.spoj import SpojPractice
from practice_platform.codeforces import CodeforcesPractice
from practice_platform.codechef import CodechefPractice
from util.datetime import get_course_week
from util.log import get_logger
import traceback
from collections import defaultdict
from csv import DictReader
from pprint import pformat
from util.common import star

LOG = get_logger("Grader")

# Main constants
# NOTE: Can't move to constants.py cuz circular dependency
CONTEST_PLATFORMS = [Codeforces(), Atcoder(), Codechef(), Dmoj(), Leetcode()]
PRACTICE_PLATFORMS = [CodeforcesPractice(), AtcoderPractice(), CodechefPractice(), SpojPractice(), UvaPractice()]


def get_users() -> List[User]:
    users = []
    with open(CACHE_PATH.joinpath("handles.csv"), "r") as f:
        reader = DictReader(f)
        for row in reader:
            if row["registered"] != "Yes":
                continue

            # Name
            first_name = row["first_name"] 
            middle_name = row["middle_name"]
            last_name = row["last_name"]
            name = first_name
            if middle_name != "N/A":
                name += (" " + middle_name)
            name += ( " " + last_name)

            # Uni
            uni = row["uni"]

            # Handles
            not_handle_headers = set(["uni", "registered", "first_name", "middle_name", "last_name"])
            handle_headers = [header for header in row.keys() if header not in not_handle_headers]
            usr_id_map = dict()
            for platform_name in handle_headers:
                value = row.get(platform_name, None)
                if value is None or value == "":
                    LOG.error(f"User: [{name}] with uni: [{uni}] has no id specified for platform: [{platform_name}]. Setting it to None for now. Needs fixing.")
                    value = None
                elif " " in value:
                    LOG.error(f"User: [{name}] with uni: [{uni}] has an invalid id: [{value}] for platform: [{platform_name}]. Setting it to None for now. Needs fixing.")
                    value = None
                usr_id_map[platform_name.strip()] = value.strip() if value is not None else value

            users.append(User(name, uni, usr_id_map))
    return users


EVENT_STR_TEMPLATE = r'"curr_dt": "{curr_dt}", "week_num": {week_num}, "uni": "{uni}", "platform_name": "{platform_name}", "is_exception": {is_exception}, "points": {points}, "event_type": "{event_type}", "event_name": "{event_name}"'
def save_grade_event(grade_file_path: Path, gd: Grading, usr: User, platform, is_exception: bool, points: int, event_type: str, event_name: str) -> None:
    event_str = EVENT_STR_TEMPLATE.format(
        curr_dt=get_curr_dt_est().isoformat(),
        week_num=gd.week_num,
        uni=usr.user_id,
        platform_name=platform.name(),
        is_exception='true' if is_exception else 'false',
        points=points,
        event_type=event_type,
        event_name=event_name)

    with open(grade_file_path, "a") as f:
        f.write("{" + event_str + "}" + "\n")



def grade_practice(gd: Grading, usr: User, platform: PracticePlatformBase, contest_solved_questions_map: Dict[str, Set[str]], grade_file_path: Path):
    practice_points = 0
    is_exception = True
    try:
        LOG.debug(f"Obtained [{contest_solved_questions_map}] for platform: [{platform.name()}]")
        practice_points = (PRACTICE_PROBLEM_MULTIPLIER * platform.successfull_submissions(gd, usr, contest_solved_questions_map))
        is_exception = False
    except Exception as e:
        traceback.print_exc()
        LOG.error(f"Exception for {platform.name()} ^")

    save_grade_event(grade_file_path, gd, usr, platform, is_exception, practice_points, 'practice', '')
    LOG.debug(f"User: [{usr.user_id}] for platform: [{platform.name()}] for practice, has points: [{practice_points}]")



def grade_contest(gd: Grading, usr: User, platform: ContestPlatformBase, ct: Contest, grade_file_path: Path) -> Set[str]:
    contest_solved_questions = set()
    contest_points = 0
    is_exception = True
    try:
        contest_submission = platform.successful_submissions(gd, ct, usr)
        contest_solved_questions = contest_submission.solved_questions
        contest_points = (CONTEST_PROBLEM_MULTIPLIER * len(contest_solved_questions))
        is_exception = False
    except Exception as e:
        traceback.print_exc()
        LOG.error(f"Exception for platform: [{platform.name()}] for contest: [{ct.contest_id}] ^")

    save_grade_event(grade_file_path, gd, usr, platform, is_exception, contest_points, 'contest', ct.contest_id)
    LOG.debug(f"User: [{usr.user_id}] for platform: [{platform.name()}] for contest: [{ct.contest_id}] has points: [{contest_points}]")
    return contest_solved_questions



def grade(week_num: int, force: bool):
    """
    This method will iterate over all registered users for each contest based platform and practice based platform and collect the number of correct submissions
    and gather points.

    It will save each point decision made as an event in the log file that methods/programs later can use to build out more stats and finalize grades.
    """

    # Some globals
    gd = Grading(week_num=week_num) # grading timeline
    PLATFORM_CONTESTS_MAP = {platform: platform.all_contests(gd) for platform in CONTEST_PLATFORMS} # Map of each platform's contests during the grading week
    ALL_USERS = get_users()
    
    print_str = pformat({platform.name(): [ct.contest_id for ct in contests] for platform, contests in PLATFORM_CONTESTS_MAP.items()}, indent=2)
    LOG.info(f"Platform contests map: [\n{print_str}\n]")
    LOG.info(f"Num users: [{len(ALL_USERS)}]")
    

    # Create grade file if not present
    grade_file_name = f"grade_{gd.week_num}.log"
    grade_file_path = CACHE_PATH.joinpath(grade_file_name)
    if not grade_file_path.exists():
        grade_file_path.touch()
    elif force:
        new_grade_file_path = CACHE_PATH.joinpath(f"grade_{gd.week_num}_old_{int(get_curr_dt_est().timestamp()*1000)}.log")
        grade_file_path.replace(new_grade_file_path)
        grade_file_path.touch()

    # Begin creating grading events
    for usr in ALL_USERS:
        star(f"\n\nGrading user: [{usr.name}] with uni: [{usr.uni}]", LOG)

        # 1. First calculate for contests. They carry a lot mote points and so in case of double counting (submission that appear as contest submissions and normal practice problems)
        # points obtained for contests take precedence.
        platform_contest_solved_questions_map = defaultdict(dict)
        for platform, contests in PLATFORM_CONTESTS_MAP.items():
            star(f"Grading contests for user: [{usr.name}] with uni: [{usr.uni}] for platform: [{platform.name()}]", LOG)

            contest_solved_questions_map = dict()
            for ct in contests: 
                # Iterate on contests in the inner most loop so that we don't get rate-limited for hitting too often (depsite our internal rate-limiting controls)
                contest_solved_questions = grade_contest(gd, usr, platform, ct, grade_file_path)
                contest_solved_questions_map[ct.contest_id] = contest_solved_questions
            
            platform_contest_solved_questions_map[platform.name()] = contest_solved_questions_map


        # 2. Once all contest calculations for a user are over, calculate for practice problems. 
        # Remember to pass submissions seen in contests on the same platform before to protect from double counting.
        for platform in PRACTICE_PLATFORMS:
            star(f"Grading practice for user: [{usr.name}] with uni: [{usr.uni}] for platform: [{platform.name()}]", LOG)
            grade_practice(gd, usr, platform, platform_contest_solved_questions_map[platform.name()], grade_file_path)



def parse_args():
    parser = argparse.ArgumentParser(description='Grader for COMS-W4995-14 Tech Interview in C++, Spring 2022')
    parser.add_argument('-w', '--week', help="Week number, ex: 5, or 6...", required=True, dest="week_num", type=int)
    parser.add_argument('-f', '--force', help="Flag to indicate to ignore older grading events and calculate afresh", dest="force", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    grade(args.week_num, args.force)