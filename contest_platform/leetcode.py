from typing import List
from model.submission import Submission
from util.web import WebRequest
from util.log import get_logger
from contest_platform.base import ContestPlatformBase, Grading, User, Contest
from datetime import datetime, timedelta
import requests as r
from util.datetime import in_between_dt, to_dt_from_ts
from constants import EST_TZINFO, CACHE_PATH
from util.common import fail
from math import ceil
import json
from pathlib import Path

LOG = get_logger("Leetcode")


class Leetcode(ContestPlatformBase):
    """
        Leetcode does not have an official API. Scraping is possible, but for things that matter
        leetcode uses simple GraphQL API calls to fetch data that seem to not need authentication.

        So, we'll try to use that for now.

        Rate-limiting of 1s per request will apply, to be respectful to this undocumented public api.
    """

    PLATFORM = "Leetcode"

    CONTESTS_URL = "https://leetcode.com/graphql"
    CONTESTS_URL_POST_REQUEST = r'{"operationName":null,"variables":{},"query":"{\n  brightTitle\n  currentTimestamp\n  allContests {\n    containsPremium\n    title\n    titleSlug\n    startTime\n    duration\n    originStartTime\n    isVirtual\n  }\n}\n"}'
    CONTESTS_URL_HEADERS = {"Content-type": "application/json"}

    RANKINGS_URL = "https://leetcode.com/contest/api/ranking/{contest_id}/?pagination={page_num}&region=global"
    RANKINGS_URL_HEADERS = {"Content-type": "application/json"}
    RANKINGS_PER_PAGE = 25
    WR = WebRequest(rate_limit_millis=2000)

    POINTS_CACHE = dict()


    def name(self):
        return Leetcode.PLATFORM


    def all_contests(self, gd: Grading) -> List[Contest]:
        """
            Leetcode's GraphQL API shows all contests at once. We'll need to filter them.

            NOTE: Because it is highly unlikely to change, for a grading week, we should probably also cache them.

            Return a list of contests.

            Sample json:
            {
                "data": {
                    "brightTitle": false,
                    "currentTimestamp": 1643758693.470451,
                    "allContests": [
                    {
                        "containsPremium": false,
                        "title": "Weekly Contest 279",
                        "cardImg": "https://assets.leetcode.com/contest/weekly-contest-279/card_img_1643515313.png",
                        "titleSlug": "weekly-contest-279",
                        "startTime": 1644114600,
                        "duration": 5400,
                        "originStartTime": 1644114600,
                        "isVirtual": false,
                    },
                    ...
        """
        
        contests = Leetcode.WR.post(Leetcode.CONTESTS_URL, data=Leetcode.CONTESTS_URL_POST_REQUEST, headers=Leetcode.CONTESTS_URL_HEADERS)
        if (contests is None) or (contests["data"] is None) or (len(contests["data"]["allContests"]) == 0):
            fail(f"No contests found", LOG)

        contests = contests["data"]["allContests"]
        curr_contests = []
        for contest in contests:
            curr_dt = to_dt_from_ts(contest["startTime"]*1000)
            if in_between_dt(curr_dt, gd.week_start_dt, gd.week_end_dt):
                curr_contests.append({**contest, "startDatetime": curr_dt})
            if curr_dt < gd.week_start_dt:
                LOG.debug(f"Breaking because contest: [{contest['title']}] started at: [{curr_dt}] and is older than: [{gd.week_start_dt}]")
                break
                
        LOG.debug(f"Contests: {[contest['title'] for contest in curr_contests]}")
        return [Contest(str(contest["titleSlug"])) for contest in curr_contests]


    def pre_process(self, gd: Grading) -> None:
        """
        Leetcode does not allow filtering on a username in its ranking list for a contest. So, we'll have to scrape all rankings
        and cache them. There are generally about 500 pages of rankings that matter for a contest (i.e. at least 1 successful submission)
        and with a rate-limiting of 1 request every 2 seconds, this is about ~15-20min for pre-processing per contest.

        Sample page: https://leetcode.com/contest/weekly-contest-278/ranking/398/
        
        Actual undocumented API request behind: https://leetcode.com/contest/api/ranking/weekly-contest-278/?pagination=398&region=global

        Sample Json:
        {
            "time": 1643766565.1494322,
            "is_past": true,
            "submissions": [
                {
                    "2261": {
                        "id": 5773459,
                        "date": 1643514918,
                        "question_id": 2261,
                        "submission_id": 630653930,
                        "status": 10,
                        "contest_id": 626,
                        "data_region": "US",
                        "fail_count": 0
                    },
                    "2274": {
                        "id": 5759547,
                        "date": 1643513147,
                        "question_id": 2274,
                        "submission_id": 630628477,
                        "status": 10,
                        "contest_id": 626,
                        "data_region": "US",
                        "fail_count": 0
                    }
                },
                ...

        """
        all_contests = self.all_contests(gd)
        for ct in all_contests:
            LOG.info(f"Pre-processing contest: [{ct.contest_id}]")
            cache_file_name = f"{Leetcode.PLATFORM}_{gd.week_num}_{ct.contest_id}.json"
            cache_file_path = CACHE_PATH.joinpath(cache_file_name)

            if cache_file_path.exists():
                LOG.info(f"Cache exists for contest: [{ct.contest_id}] for week: [{gd.week_num}] at: [{cache_file_path}]. Skipping..")
                continue

            page_num_total = float('inf')
            page_num = 1
            cache_dict = dict()
            short_circuit = False
            while (not short_circuit) and (page_num <= page_num_total):     
                rankings_url = Leetcode.RANKINGS_URL.format(contest_id=ct.contest_id, page_num=page_num)
                LOG.debug(f"Rankings url is: [{rankings_url}]")

                rankings = Leetcode.WR.get(rankings_url)
                if (rankings is None) or ("submissions" not in rankings) or ("total_rank" not in rankings):
                    fail(f"No rankings/submissions found for url: [{rankings_url}]", LOG)

                if (len(rankings["submissions"]) == 0) or (len(rankings["total_rank"]) == 0):
                    LOG.debug(f"Empty submissions/total_rank found for url: [{rankings_url}]")
                    short_circuit = True
                    break
                
                submissions = rankings["submissions"]
                ranks = rankings["total_rank"]
                questions = {str(question["question_id"]): question["title"] for question in rankings["questions"]}

                if page_num_total == float('inf'):
                    page_num_total = ceil(rankings["user_num"]/Leetcode.RANKINGS_PER_PAGE)

                for i, rank in enumerate(ranks):
                    user_name = rank["username"]
                    solved_questions = [str(question_id) + " -- " + questions[str(question_id)] for question_id, submission in submissions[i].items()]
                    LOG.debug(f"user: [{user_name}] solved these questions: [{solved_questions}]")
                    cache_dict[user_name] = solved_questions

                    # Short circuit if user had 0 submissions, as that is simply 0 points
                    if len(submissions[i]) == 0:
                        LOG.debug(f"Short circuiting at page_num: [{page_num}] with url: [{rankings_url}] from user: [{user_name}] because 0 submissions have started.")
                        short_circuit = True
                        break

                page_num += 1
            
            
            with open(cache_file_path, "w") as f:
                f.write(json.dumps(cache_dict))
                LOG.info(f"Cached results for week: [{gd.week_num}] and contest: [{ct.contest_id}] at: [{cache_file_name}]")
        
    
    def __get_points(self, usr: User, ct: Contest) -> Submission:
        if usr.user_id not in Leetcode.LEETCODE_POINTS_CACHE[ct.contest_id]:
            LOG.info(f"user: [{usr.user_id}] not found in points cache for contest: [{ct.contest_id}].")
            return Submission()
        
        val = Leetcode.LEETCODE_POINTS_CACHE[ct.contest_id][usr.user_id]
        LOG.debug(f"user: [{usr.user_id}] in contest: [{ct.contest_id}] solved these questions: [{val}]")
        return Submission(set(val))
        

    def successful_submissions(self, gd: Grading, ct: Contest, usr: User) -> Submission:
        """
            This bit it odd. Leetcode rankings do not allow you to search based on user_id,
            so there is no clear API (documented or otherwise).

            So, there are 2 options:
            1. OCR the submissions picture, get the user's rank, guess the page number on which the rank
               might appear on leetcode rankings page and cross-check that.
            2. Pre-process all contest rankings. There are about 500 pages of rankings per contest to scrape.
               Could be a background process that does this as soon as previous grading week deadline ends.

            
            Going the pre-processing route for now.

            NOTE: With rate-limiting pre-processing can take a lot of time here, so best to pre-process even earlier
        """

        if ct.contest_id not in Leetcode.POINTS_CACHE:
            cache_file_name = f"{Leetcode.PLATFORM}_{gd.week_num}_{ct.contest_id}.json"
            cache_file_path = CACHE_PATH.joinpath(cache_file_name)
            if not cache_file_path.exists():
                fail(f"Pre-processed cache missing for contest: [{ct.contest_id}] for week: [{gd.week_num}]. Please perform pre-processing first for this platform", LOG)
            with open(cache_file_path, "r") as f:
                Leetcode.POINTS_CACHE[ct.contest_id] = json.loads(f.read())

        return self.__get_points(usr, ct)

        
