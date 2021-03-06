from typing import List
from model.submission import Submission
from util.web import WebRequest
from util.log import get_logger
from contest_platform.base import ContestPlatformBase, Grading, User, Contest
from datetime import datetime, timedelta
import requests as r
from util.datetime import in_between_dt, to_dt_from_ts
from constants import EST_TZINFO, IST_TZINFO
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

    # Each parent contest has a bunch of child contests based on ratings - div1, div2 etc, and some of those
    # child contests maybe unrated.
    # This is the URL to fetch list of child contests by providing parent contest code, and checking out details
    # about the child contest by providing the child contest code 
    CHILD_CONTESTS_URL = "https://www.codechef.com/api/contests/{contest_code}"
    
    # https://www.codechef.com/api/contests/COOK127?v=1643691157039
    # https://www.codechef.com/api/rankings/START22A?sortBy=rank&order=asc&search=jo3kerr&page=1&itemsPerPage=25
    SUBMISSIONS_URL = "https://www.codechef.com/rankings/{child_contest_id}?order=asc&search={user_id}&sortBy=rank"
    WR = WebRequest(rate_limit_millis=2000)


    def name(self):
        return Codechef.PLATFORM


    def __get_dt(self, text: str) -> datetime:
        dt = datetime.strptime(text, "%d-%m-%Y %H:%M:%S")
        dt = dt.replace(tzinfo=IST_TZINFO)
        dt = dt.astimezone(EST_TZINFO)
        return dt


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
                curr_contest_start_dt = datetime.fromisoformat(curr_contest["contest_start_date_iso"])
                curr_contest_end_dt = datetime.fromisoformat(curr_contest["contest_end_date_iso"])
                # If start time of contest is b/w grading week, or end time of contest is b/w grading week, or the grading week is in b/w the super long contest (possibly spanning multiple weeks)
                if in_between_dt(curr_contest_start_dt, gd.week_start_dt, gd.week_end_dt) or in_between_dt(curr_contest_end_dt, gd.week_start_dt, gd.week_end_dt) or in_between_dt(gd.week_start_dt, curr_contest_start_dt, curr_contest_end_dt):
                    parent_contests.append(curr_contest)

            if datetime.fromisoformat(curr_contests[-1]["contest_end_date_iso"]) < gd.week_start_dt:
                LOG.debug(f"Breaking because contest end date: [{curr_contests[-1]['contest_end_date_iso']}] is earlier that grading start week: [{gd.week_start_dt}]")
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
            child_contests_url = Codechef.CHILD_CONTESTS_URL.format(contest_code=parent_contest_code)
            child_contests_resp = Codechef.WR.get(child_contests_url)

            if (child_contests_resp is None) or (child_contests_resp["status"] != "success"):
                fail(f"No child contests found for parent contest: {parent_contest_code}", LOG)

            for child_contest_obj in child_contests_resp["child_contests"].values():
                child_contest_code = child_contest_obj["contest_code"]
                child_contest_url = Codechef.CHILD_CONTESTS_URL.format(contest_code=child_contest_code)
                child_contest_resp = Codechef.WR.get(child_contest_url)

                if (child_contest_resp is None) or (child_contest_resp['status'] != "success"):
                    fail(f"Child contests details not found: {child_contest_code}", LOG)

                child_contest_unrated = "Unrated" in child_contest_resp["name"]
                LOG.debug(f"For Parent contest: [{parent_contest_code}] a child contest is: [{child_contest_code}], and is: [{'unrated' if child_contest_unrated else 'rated'}]")
                if not child_contest_unrated:
                    child_contests.append({**parent_contest, "child_contest_code": child_contest_code})


        contests = [{**contest, "startDatetime": datetime.fromisoformat(contest["contest_end_date_iso"])} for contest in child_contests]
        # Already filtered more accurately above (parent contests), so need for the following line.
        # contests = [contest for contest in contests if in_between_dt(contest["startDatetime"], gd.week_start_dt, gd.week_end_dt)]
        LOG.debug(f"Contests: {[c['child_contest_code'] for c in contests]}")
        return [Contest(str(contest["child_contest_code"])) for contest in contests]
        

    def successful_submissions(self, gd: Grading, ct: Contest, usr: User) -> Submission:
        """
            This bit it odd. Despite the clear and simple undocumented API, this api needs
            something more to work in isolation. It returns an error despite setting cookies and csrfTokens correctly.
            
            So, we'll need to use selenium web scraping here.
            
            Sample: https://www.codechef.com/rankings/COOK127A?order=asc&search=marckess&sortBy=rank
        """
        usr_handle = usr.handle(self.name())
        submissions_url = Codechef.SUBMISSIONS_URL.format(child_contest_id=ct.contest_id , user_id=usr_handle)
        LOG.debug(f"Submission url: {submissions_url}")


        driver = Codechef.WR.scrape(submissions_url)

        # Get user's accepted solutions
        # Need to filter these trs a little more because codechef returns prefix matches along with exact matches for username
        direct_tr_vals = driver.find_elements_by_css_selector("table[class*='MuiTable-root'] > tbody > tr")

        # With the latest update to Codechef, it waits a little more before loading the ranks.
        # So, wait until it has loaded them
        if any(["Loading" in tr_val.text for tr_val in direct_tr_vals]):
            Codechef.WR.wait_until_presence_of(driver, "a[href*='https://www.codechef.com/users']")

        # Collect trs again, because DOM could've updated and resulted in stale elements (i.e older tr_vals getting deleted from the page)
        direct_tr_vals = driver.find_elements_by_css_selector("table[class*='MuiTable-root'] > tbody > tr")
        LOG.debug(f"Num direct tr vals: {len(direct_tr_vals)}")
        tr_vals = []
        for tr_val in direct_tr_vals:
            user_handle_a_tags = tr_val.find_elements_by_css_selector("td div > a[href*='https://www.codechef.com/users']")
            LOG.debug(f"Num user handle a tags: {len(user_handle_a_tags)}")
            if len(user_handle_a_tags) == 1:
                user_handle_a_tag = user_handle_a_tags[0]
                user_link = user_handle_a_tag.get_attribute("href")
                LOG.debug(f"User link: {user_link}")
                if user_link.split("/")[-1] == usr_handle:
                    tr_vals.append(tr_val)

        LOG.debug(f"Num tr found: {len(tr_vals)}")
        if len(tr_vals) not in [0, 1]:
            fail(f"Unexpected count: [{len(tr_vals)}] of ranking found for: [{submissions_url}]", LOG)
        if len(tr_vals) == 0:
            LOG.debug(f"No submissions found for user: [{usr_handle}] in contest: [{ct.contest_id}]")
            return Submission()
        td_vals = tr_vals[0].find_elements_by_css_selector("td")
        LOG.debug(f"Num div found: {len(td_vals)}")


        # Get table headers for problem names
        th_vals = driver.find_elements_by_css_selector("table[class*='MuiTable-root'] > thead > tr > th")
        LOG.debug(f"Num th found: {len(th_vals)}")

        # Calc offset
        # The 4th/5th name onwards are the problem names. ex: https://www.codechef.com/rankings/COOK137C?order=asc&search=idm2114&sortBy=rank vs https://www.codechef.com/rankings/START23A?order=asc&search=idm2114&sortBy=rank
        offset=3
        if len(th_vals[3].find_elements_by_css_selector("div > a")) == 0:
            offset += 1

        # Push td and th offset nums
        td_vals = td_vals[offset:]
        th_vals = th_vals[offset:]

        # Get on with problems names and score    
        problem_names = [th_val.find_element_by_css_selector("a").get_attribute("href").split("problems/")[1].strip() for th_val in th_vals]
        LOG.debug(f"problem names: {problem_names}")

        solved_questions = set()
        for i, val in enumerate(td_vals):
            LOG.debug(f"[MAJOR*****] val: {val.text}")
            has_answered = val.find_elements_by_css_selector("a")
            if len(has_answered) not in [0, 1]:
                fail(f"Unexpected count: [{len(has_answered)}] of answers found at: [{submissions_url}]", LOG)
            if len(has_answered) == 1:
                LOG.debug(f"[MAJOR NEXT*****] len: {len(has_answered)}, first val: {has_answered[0].text}")

                # Because certain codechef contests (such as LONG) occur on weekends over friday, saturday and more,
                # the submissions leak across 2 consecutive grading weeks, and risk getting double counted.
                # So, we gotta check if each submission is within the grading week dates.
                solution_href = has_answered[0].get_attribute("href")
                LOG.debug(f"Fetching solution for a few more checks: [{solution_href}]")
                driver2 = Codechef.WR.scrape(solution_href)
                lis = driver2.find_elements_by_css_selector("div[class*='tab-pane solution-info'] ul > li")
                if len(lis) <= 0:
                    fail(f"Unexpected count: [{len(lis)}] for list in solutions pane")
                li = lis[0]
                solution_dt = self.__get_dt(li.text)
                if in_between_dt(solution_dt, gd.week_start_dt, gd.week_end_dt):
                    solved_questions.add(problem_names[i])
                else:
                    LOG.debug(f"Problem: [{problem_names[i]}] was submitted at [{solution_dt}] which is not within the current grading week: [{gd.week_num}], so not counting it.")

                if driver2 is not None:
                    driver2.quit()

        if driver is not None:
            driver.quit()

        LOG.debug(f"User [{usr_handle}] in contest [{ct.contest_id}] solved these questions: [{solved_questions}]")
        return Submission(solved_questions)
