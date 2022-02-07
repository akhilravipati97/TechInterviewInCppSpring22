import argparse
from collections import defaultdict
from typing import Dict
from constants import CACHE_PATH
from util.common import fail
from util.log import get_logger
from grader import CONTEST_PLATFORMS, PRACTICE_PLATFORMS
import json
from csv import DictWriter


LOG = get_logger("CalculatePoints")



def parse_args():
    parser = argparse.ArgumentParser(description='Events preprocessor - to generate graders')
    parser.add_argument('-w', '--week', help="Week number, ex: 5, or 6...", required=True, dest="week_num", type=int)
    return parser.parse_args()


def calculate(week_num: int):
    grade_sheet_path = CACHE_PATH.joinpath(f"grades_{week_num}.csv")
    grade_events_path = CACHE_PATH.joinpath(f"grade_{week_num}.log")
    
    if not grade_events_path.exists():
        fail(f"Grading events file: [{grade_events_path}] does not exist", LOG)

    if grade_sheet_path.exists():
        LOG.warning(f"Grade sheet: [{grade_sheet_path}] already exists")
        val = input("Overwrite? (y/n): ")
        if val != "y":
            exit(-1)

    # Gather into map
    usr_points_map = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    num_exceptions = 0
    with open(grade_events_path, "r") as f:
        for line in f:
            LOG.debug(f"line: {line}")
            data = json.loads(line)
            uni = data["uni"]
            platform_name = data["platform_name"]
            event_type = data["event_type"]
            points = int(data["points"])
            num_exceptions += int(bool(data["is_exception"]))
            usr_points_map[uni][event_type][platform_name] += points

    if num_exceptions:
        LOG.error(f"There are [{num_exceptions}] exceptions in grade log!!")

    # finalize headers
    contest_platform_headers = sorted([platform.name() for platform in CONTEST_PLATFORMS])
    practice_platform_headers = sorted([platform.name() for platform in PRACTICE_PLATFORMS])

    final_headers = ["uni"]
    final_headers += [ct + "_contest" for ct in contest_platform_headers]
    final_headers += [pt + "_practice" for pt in practice_platform_headers]
    final_headers += ["Topcoder_contest", "Topcode_practice", "Leetcode_practice", "Kattis_practice"] # manual - auto grader does not cover these yet - dictwriter will fill in 'MANUAL' in each row
    final_headers += ["contest_points", "practice_points", "total_points"]

    # begin creating csv rows as dicts
    rows = []
    for uni, event_type_map in usr_points_map.items():
        row = {"uni": uni}

        contest_points = 0
        for platform_name in contest_platform_headers:
            row[platform_name + "_contest"] = event_type_map["contest"][platform_name]
            contest_points += event_type_map["contest"][platform_name]
        row["contest_points"] = contest_points

        practice_points = 0
        for platform_name in practice_platform_headers:
            row[platform_name + "_practice"] = event_type_map["practice"][platform_name]
            practice_points += event_type_map["practice"][platform_name]
        row["practice_points"] = practice_points

        row["total_points"] = contest_points + practice_points
        rows.append(row)


    # write the rows into csv
    with open(grade_sheet_path, "w", newline='', encoding='utf-8') as f:
        writer = DictWriter(f, fieldnames=final_headers, restval='MANUAL')
        writer.writeheader()
        writer.writerows(rows)

    LOG.info("Done.")

        





if __name__ == "__main__":
    args = parse_args()
    calculate(args.week_num)