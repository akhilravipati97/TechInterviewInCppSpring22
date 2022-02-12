from csv import DictReader, DictWriter
from pathlib import Path
from constants import CACHE_PATH
from util.log import get_logger
from util.common import fail
import argparse

LOG = get_logger("PopulateGradebook")

def parse_args():
    parser = argparse.ArgumentParser(description='Events preprocessor - to generate graders')
    parser.add_argument('-w', '--week', help="Week number, ex: 5, or 6...", required=True, dest="week_num", type=int)
    parser.add_argument('-c', '--gradebook', help="Path to gradebook csv exported from courseworks", required=True, dest="gradebook_path")
    return parser.parse_args()


def populate(week_num: int, gradebook_path: str):
    gradebook_path = Path(gradebook_path)
    new_gradebook_path = CACHE_PATH.joinpath(f"courseworks_new_grades_{week_num}.csv")
    calculated_grades_path = CACHE_PATH.joinpath(f"grades_{week_num}.csv")

    # file checks
    if not gradebook_path.exists():
        fail(f"Courseworks gradebook path: [{gradebook_path}] does not exist.", LOG)

    if not calculated_grades_path.exists():
        fail(f"Calculated grades csv file: [{calculated_grades_path}] does not exist.", LOG)
    
    if new_gradebook_path.exists():
        fail(f"New courseworks gradebook path: [{new_gradebook_path}] already exists.", LOG)

    
    # read calculated grades
    uni_points = dict()
    with open(calculated_grades_path, "r", encoding='utf-8', newline='') as f:
        reader = DictReader(f)
        for row in reader:
            final_points = row["final_points"]
            final_points = final_points.strip() if final_points is not None else final_points
            uni = row["uni"]
            uni = uni.strip() if uni is not None else uni

            if final_points in [None, "MANUAL", ""]:
                fail(f"For uni: [{uni}], final_points: [{final_points}] is invalid.", LOG)
            
            if uni is None or uni == "":
                fail(f"Invalid uni: [{uni}] for row: [{row}]")

            uni_points[uni] = float(final_points)
    

    # read gradebook csv
    gradebook_rows = []
    with open(gradebook_path, "r", encoding='utf-8', newline='') as f:
        reader = DictReader(f)
        gradebook_rows = list(reader)
    if len(gradebook_rows) == 0:
        fail(f"Unexpected number of rows in gradebook", LOG)
    LOG.debug(f"Gradebook row keys: [{gradebook_rows[0].keys()}]")
    LOG.debug(f"Gradebook row: [{gradebook_rows[2]}]")

    # update gradebook rows    
    grading_week_column = [key for key in gradebook_rows[0].keys() if f"Week #{week_num}" in key]
    if len(grading_week_column) != 1:
        fail(f"Unexpected grading week columns found: [{grading_week_column}]", LOG)
    grading_week_column = grading_week_column[0]
    LOG.info(f"Using grading week column: [{grading_week_column}]")

    for row in gradebook_rows:
        uni = row["SIS User ID"]
        if uni in [None, ""]:
            continue

        if uni not in uni_points:
            LOG.error(f"Uni from gradebook: [{uni}] not present in grades calculated by autograder\
- likely an observing student (or) they were not registered for that week. Filling in zero for now. But PLEASE CHECK.")
        val = uni_points.get(uni, 0)
        row[grading_week_column] = val
    
    # write gradebook rows
    with open(new_gradebook_path, "w", encoding='utf-8', newline='') as f:
        writer = DictWriter(f, fieldnames=list(gradebook_rows[0].keys()))
        writer.writeheader()
        writer.writerows(gradebook_rows)

    LOG.info(f"Done. Check file: [{new_gradebook_path}].")



if __name__ == "__main__":
    args = parse_args()
    populate(args.week_num, args.gradebook_path)