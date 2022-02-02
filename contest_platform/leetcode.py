from typing import List
from util.web import WebRequest
from util.log import get_logger
from contest_platform.base import PlatformBase, Grading, User, Contest
from datetime import datetime, timedelta
import requests as r
from util.datetime import in_between_dt, to_dt_from_ts
from constants import EST_TZINFO
from util.common import fail

LOG = get_logger("Leetcode")


class Leetcode(PlatformBase):
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

    # Each parent contest has a bunch of child contests based on ratings - div1, div2 etc.
    CHILD_CONTESTS_URL = "https://www.codechef.com/api/contests/{contest_code}"
    
    # https://www.codechef.com/api/contests/COOK127?v=1643691157039
    # https://www.codechef.com/api/rankings/START22A?sortBy=rank&order=asc&search=jo3kerr&page=1&itemsPerPage=25
    SUBMISSIONS_URL = "https://www.codechef.com/rankings/{child_contest_id}?order=asc&search={user_id}&sortBy=rank"
    WR = WebRequest(rate_limit_millis=1000)


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
        
        contests = Leetcode.WR.post(Leetcode.CONTESTS_URL, data=Leetcode.CONTESTS_URL_POST_REQUEST, headers=Leetcode.CONTESTS_URL_HEADERS).json()
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
        return [Contest(str(contest["title"])) for contest in curr_contests]
        

    def successful_submissions(self, gd: Grading, ct: Contest, usr: User) -> int:
        """
            This bit it odd. Leetcode rankings do not allow you to search based on user_id,
            so there is no clear API (documented or otherwise).

            So, there are 2 options:
            1. OCR the submissions picture, get the user's rank, guess the page number on which the rank
               might appear on leetcode rankings page and cross-check that.
            2. Pre-process all contest rankings. There are about 500 pages of rankings per contest to scrape.
               Could be a background process that does this as soon as previous grading week deadline ends.
            
            
            Sample: https://leetcode.com/contest/weekly-contest-278/ranking/398/
        """
        return 0

        
