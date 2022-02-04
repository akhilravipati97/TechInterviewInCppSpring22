from typing import List
from model.submission import Submission
from util.web import WebRequest
from util.log import get_logger
from contest_platform.base import ContestPlatformBase, Grading, User, Contest
from datetime import datetime, timedelta
import requests as r
from util.datetime import in_between_dt, to_dt_from_ts
from constants import EST_TZINFO
from util.common import fail

LOG = get_logger("Codechef")


class Codechef(ContestPlatformBase):
    """
        Codechef does not have an official API. Scraping is possible, but for things that matter
        codechef uses simple API calls to fetch data that seem to not need authentication.

        So, we'll try to use that for now.

        Rate-limiting of 1s per request will apply, to be respectful to this undocumented public api.
    """

    PLATFORM = "Codechef"

    # These parent contests are reported 20 at a time
    CONTESTS_URL = "https://www.codechef.com/api/list/contests/past?sort_by=START&sorting_order=desc&offset={offset_count}&mode=premium"
    CONTESTS_URL_OFFSET_DIFF = 20

    # Each parent contest has a bunch of child contests based on ratings - div1, div2 etc.
    CHILD_CONTESTS_URL = "https://www.codechef.com/api/contests/{contest_code}"
    
    # https://www.codechef.com/api/contests/COOK127?v=1643691157039
    # https://www.codechef.com/api/rankings/START22A?sortBy=rank&order=asc&search=jo3kerr&page=1&itemsPerPage=25
    SUBMISSIONS_URL = "https://www.codechef.com/rankings/{child_contest_id}?order=asc&search={user_id}&sortBy=rank"
    WR = WebRequest(rate_limit_millis=1000)


    def name(self):
        return Codechef.PLATFORM


    def all_contests(self, gd: Grading) -> List[Contest]:
        """
            Codechef's API shows 20 past contests at a time (desc order). We'll need to keep scanning until
            the contest's between our dates are found.

            Return a list of contests.

            Sample json:
            {
                "status": "success",
                "message": "past contests list",
                "contests": [
                    {
                    "contest_code": "LTIME104",
                    "contest_name": "January Lunchtime 2022",
                    "contest_start_date": "29 Jan 2022  20:00:00",
                    "contest_end_date": "29 Jan 2022  23:00:00",
                    "contest_start_date_iso": "2022-01-29T20:00:00+05:30",
                    "contest_end_date_iso": "2022-01-29T23:00:00+05:30",
                    "contest_duration": "180",
                    "distinct_users": 16809
                    },
                ...
        """

        curr_offset = 0
        parent_contests = []
        while True:
            contests_url = Codechef.CONTESTS_URL.format(offset_count=curr_offset)
            LOG.debug(f"Calling for contests_url: {contests_url}")

            curr_contests = Codechef.WR.get(contests_url)
            if (curr_contests is None) or (curr_contests["status"] != "success"):
                fail(f"Contests failed to find for {contests_url}. Response: {curr_contests}", LOG)

            curr_contests = curr_contests["contests"]
            for curr_contest in curr_contests:
                curr_contest_dt = datetime.fromisoformat(curr_contest["contest_start_date_iso"])
                if in_between_dt(curr_contest_dt, gd.week_start_dt, gd.week_end_dt):
                    parent_contests.append(curr_contest)

            if datetime.fromisoformat(curr_contests[-1]["contest_start_date_iso"]) < gd.week_start_dt:
                LOG.debug(f"Breaking because {curr_contests[-1]['contest_start_date_iso']} is older that {gd.week_start_dt}")
                break
            else:
                curr_offset += Codechef.CONTESTS_URL_OFFSET_DIFF

        if len(parent_contests) == 0:
            fail(f"No contests found", LOG)


        """
        Child contests data:
        "child_contests": {
            "div_1": {
            "div": {
                "code": "div_1",
                "min_rating": 2000,
                "max_rating": 50000,
                "name": "Division 1",
                "description": "Users with rating above 2000"
            },
            "division_system": 3,
            "contest_code": "COOK127A",
            "contest_link": "/COOK127A"
            },
            ...
        """
        
        child_contests = []
        for parent_contest in parent_contests:
            parent_contest_code = parent_contest["contest_code"]
            child_contest_url = Codechef.CHILD_CONTESTS_URL.format(contest_code=parent_contest_code)
            child_contest_resp = Codechef.WR.get(child_contest_url)

            if (child_contest_resp is None) or (child_contest_resp["status"] != "success"):
                fail(f"No child contests found for parent contest: {parent_contest_code}")

            for child_contest_obj in child_contest_resp["child_contests"].values():
                child_contest_code = child_contest_obj["contest_code"]
                LOG.debug(f"For Parent contest: [{parent_contest_code}] a child contest is: [{child_contest_code}]")
                child_contests.append({**parent_contest, "child_contest_code": child_contest_code})


        contests = [{**contest, "startDatetime": datetime.fromisoformat(contest["contest_start_date_iso"])} for contest in child_contests]
        contests = [contest for contest in contests if in_between_dt(contest["startDatetime"], gd.week_start_dt, gd.week_end_dt)]
        LOG.debug(f"Contests: {[c['child_contest_code'] for c in contests]}")
        return [Contest(str(contest["child_contest_code"])) for contest in contests]
        

    def successful_submissions(self, gd: Grading, ct: Contest, usr: User) -> Submission:
        """
            This bit it odd. Despite the clear and simple undocumented API, this api needs
            something more to work in isolation. It returns an error despite setting cookies and csrfTokens correctly.
            
            So, we'll need to use selenium web scraping here.
            
            Sample: https://www.codechef.com/rankings/COOK127A?order=asc&search=marckess&sortBy=rank
        """

        submissions_url = Codechef.SUBMISSIONS_URL.format(child_contest_id=ct.contest_id , user_id=usr.user_id)
        LOG.debug(f"Submission url: {submissions_url}")


        driver = Codechef.WR.scrape(submissions_url)

        # Get user's accepted solutions
        tr_vals = driver.find_elements_by_css_selector("table[class='dataTable'] > tbody > tr")
        LOG.debug(f"Num tr found: {len(tr_vals)}")
        if len(tr_vals) not in [0, 1]:
            fail(f"Unexpected count: [{len(tr_vals)}] of ranking found for: [{submissions_url}]")
        if len(tr_vals) == 0:
            LOG.debug(f"No submissions found for user: [{usr.user_id}] in contest: [{ct.contest_id}]")
            return 0
        td_vals = tr_vals[0].find_elements_by_css_selector("td")
        LOG.debug(f"Num div found: {len(td_vals)}")
        td_vals = td_vals[4:] # The 5th onwards are the actual problems


        # Get table headers for problem names
        th_vals = driver.find_elements_by_css_selector("table[class='dataTable'] > thead > tr > th")
        LOG.debug(f"Num th found: {len(th_vals)}")
        th_vals = th_vals[4:] # The 5th name onwards are the problem names
        problem_names = [th_val.find_element_by_css_selector("a > div:nth-child(2)").text.strip() for th_val in th_vals]
        LOG.debug(f"problem names: {problem_names}")


        solved_questions = set()
        for i, val in enumerate(td_vals):
            LOG.debug(f"[MAJOR*****] val: {val.text}")
            has_answered = val.find_elements_by_css_selector("div > a")
            if len(has_answered) > 0:
                LOG.debug(f"[MAJOR NEXT*****] len: {len(has_answered)}, first val: {has_answered[0].text}")
                solved_questions.add(problem_names[i])

        LOG.debug(f"User [{usr.user_id}] in contest [{ct.contest_id}] solved these questions: [{solved_questions}]")
        return Submission(solved_questions)
