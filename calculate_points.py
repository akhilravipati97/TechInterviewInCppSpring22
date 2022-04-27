import argparse
from collections import defaultdict
from typing import Dict
from constants import CACHE_PATH
from util.common import fail
from util.log import get_logger
from grader import CONTEST_PLATFORMS, PRACTICE_PLATFORMS
import json
from csv import DictWriter, DictReader


LOG = get_logger("CalculatePoints")



def parse_args():
    parser = argparse.ArgumentParser(description='Events preprocessor - to generate grades')
    parser.add_argument('-w', '--week', help="Week number, ex: 5, or 6...", required=True, dest="week_num", type=int)
    parser.add_argument('-u', '--uni', help="For a particular uni (eg: ar4160, ak3232)", dest="uni")
    parser.add_argument('-p', '--platform', help="For a particular platform (eg: Leetcode, Codeforces, Spoj)", dest="platform_name")
    return parser.parse_args()


def prepare_file_name(prefix: str, extension: str, week_num: int, uni: str, platform_name: str) -> str:
    # Create grade file if not present
    file_name = f"{prefix}_{week_num}"
    if uni is not None and uni != "":
        file_name += f"_{uni}"
    if platform_name is not None and platform_name != "":
        file_name += f"_{platform_name}"
    file_name += f".{extension}"
    return file_name


def calculate(week_num: int, uni: str, platform_name: str):
    # Create grade file if not present
    grade_sheet_name = prepare_file_name("grades", "csv", week_num, uni, platform_name)
    grade_sheet_path = CACHE_PATH.joinpath(grade_sheet_name) #(f"grades_{week_num}.csv")

    grade_events_name = prepare_file_name("grading_events", "log", week_num, uni, platform_name)
    grade_events_path = CACHE_PATH.joinpath(grade_events_name) #(f"grading_events_{week_num}.log")

    uni_to_courseworks_path = CACHE_PATH.joinpath("uni_courseworks_id.csv")
    
    if not grade_events_path.exists():
        fail(f"Grading events file: [{grade_events_path}] does not exist", LOG)

    if not uni_to_courseworks_path.exists():
        fail(f"Uni to courseworks file: [{uni_to_courseworks_path}] does not exist", LOG)

    if grade_sheet_path.exists():
        LOG.warning(f"Grade sheet: [{grade_sheet_path}] already exists")
        val = input("Overwrite? (y/n): ")
        if val != "y":
            exit(-1)

    # Create uni to courseworks id map
    uni_to_courseworks_id = dict()
    uni_to_name = dict()
    name_idx = dict()
    with open(uni_to_courseworks_path, 'r', encoding='utf-8', newline='') as f:
        reader = DictReader(f)
        for i, row in enumerate(reader):
            print(row)
            uni_to_courseworks_id[row["uni"]] = row["courseworks_id"]
            uni_to_name[row["uni"]] = row["name"]
            name_idx[row["name"]] = i

    # Gather into map
    usr_points_map = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    num_exceptions = 0
    with open(grade_events_path, "r", encoding='utf-8') as f:
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

    # finalize headers.
    # final_headers should be ordered in the way we wanna see in the csv
    contest_platform_headers = sorted([platform.name() for platform in CONTEST_PLATFORMS])
    practice_platform_headers = sorted([platform.name() for platform in PRACTICE_PLATFORMS])

    final_headers = ["uni", "name", "courseworks_id"]
    final_headers += ["final_points", "comments", "private_comments"]
    final_headers += ["total_contest_points", "total_practice_points", "total_points"]
    final_headers += [ct + "_contest" for ct in contest_platform_headers]
    final_headers += [pt + "_practice" for pt in practice_platform_headers]
    final_headers += ["Topcoder_contest", "Topcode_practice", "Leetcode_practice", "Kattis_practice"] # manual - auto grader does not cover these yet - dictwriter will fill in 'MANUAL' in each row

    # begin creating csv rows as dicts
    rows = []
    for uni, event_type_map in usr_points_map.items():
        row = {"uni": uni, "name": uni_to_name[uni], "courseworks_id": uni_to_courseworks_id[uni]}

        contest_points = 0
        for platform_name in contest_platform_headers:
            row[platform_name + "_contest"] = event_type_map["contest"][platform_name]
            contest_points += event_type_map["contest"][platform_name]
        row["total_contest_points"] = contest_points

        practice_points = 0
        for platform_name in practice_platform_headers:
            row[platform_name + "_practice"] = event_type_map["practice"][platform_name]
            practice_points += event_type_map["practice"][platform_name]
        row["total_practice_points"] = practice_points

        row["total_points"] = contest_points + practice_points
        row["comments"] = ""
        row["private_comments"] = ""
        rows.append(row)


    # write the rows into csv
    # NOTE: Courseworks outputs submissions ordered by name as seen in the uni_courseworks_id.csv
    #       So, we gotta sort our rows similarly.
    rows.sort(key=lambda x: name_idx[x["name"]])
    with open(grade_sheet_path, "w", newline='', encoding='utf-8') as f:
        writer = DictWriter(f, fieldnames=final_headers, restval='MANUAL')
        writer.writeheader()
        writer.writerows(rows)

    LOG.info(f"Done. See file: {grade_sheet_path}")

        





if __name__ == "__main__":
    args = parse_args()
    calculate(args.week_num, args.uni, args.platform_name)