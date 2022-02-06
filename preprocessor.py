from contest_platform.leetcode import Leetcode
from model.grading import Grading
import argparse

PRE_PROCESS_PLATFORMS = [Leetcode()]

def parse_args():
    parser = argparse.ArgumentParser(description='Grading preprocessor.')
    parser.add_argument('-w', '--week', help="Week number, ex: 5, or 6...", required=True, dest="week_num", type=int)
    return parser.parse_args()

def preprocess(gd: Grading) -> None:
    for platform in PRE_PROCESS_PLATFORMS:
        platform.pre_process(gd)


if __name__ == "__main__":
    args = parse_args()
    preprocess(Grading(week_num=args.week_num))