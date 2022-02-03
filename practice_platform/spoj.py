from distutils.log import debug
from re import sub
from webbrowser import get
from constants import UTC_TZINFO
from util.datetime import to_dt_from_ts
from datetime import datetime
from model.user import User
from model.grading import Grading
from practice_platform.base import PracticePlatformBase
from util.web import WebRequest
from util.common import fail
from util.log import get_logger
from util.datetime import in_between_dt

LOG = get_logger("Spoj")


class Spoj(PracticePlatformBase):
    """
    Spoj doesn't seem to have an API, documented or otherwise. We'll have to scrape.
    """

    PLATFORM = "Spoj"

    # NOTE: Results are paginated, with a limit of 20 per page. Results are in descending order of time
    # so we can short-circuit
    SUBMISSIONS_PER_PAGE_LIMIT = 20
    SUBMISSIONS_URL = "https://www.spoj.com/status/{user_id}/all/start={submission_count}"

    WR = WebRequest(rate_limit_millis=1000)

    def name(self) -> str:
        return Spoj.PLATFORM


    def successfull_submissions(self, gd: Grading, usr: User) -> int:
        """
        We use the submissions url to fetch as many submissions as there are within a time frame.
        """

        short_circuit = False
        submission_count = 0
        solved_questions = set()
        while not short_circuit:
            submissions_url = Spoj.SUBMISSIONS_URL.format(user_id=usr.user_id, submission_count=submission_count)
            LOG.debug(f"Submissions url: [{submissions_url}]")
        
            driver = Spoj.WR.scrape(submissions_url)
            tr_vals = driver.find_elements_by_css_selector("table > tbody > tr")
            LOG.debug(f"len tr_vals: [{len(tr_vals)}]")
            if len(tr_vals) > Spoj.SUBMISSIONS_PER_PAGE_LIMIT:
                LOG.warn(f"more tr_vals found: [{len(tr_vals)}] than expected: [{Spoj.SUBMISSIONS_PER_PAGE_LIMIT}]")
            if len(tr_vals) == 0:
                break

            for tr_val in tr_vals:
                td_vals = tr_val.find_elements_by_css_selector("td")
                # NOTE: It is one hour UTC apparently, but shouldn't be that bad an idea to just assume UTC for now
                curr_dt = datetime.fromisoformat(td_vals[1].find_element_by_css_selector("span").text).replace(tzinfo=UTC_TZINFO)
                problem_id = td_vals[2].find_element_by_css_selector("a").get_attribute("title")
                status = str(td_vals[3].get_attribute("status"))

                if in_between_dt(curr_dt, gd.week_start_dt, gd.week_end_dt) and status == "15":
                    solved_questions.add(problem_id)

                if curr_dt < gd.week_start_dt:
                    LOG.debug(f"Breaking because {curr_dt} is older that {gd.week_start_dt}")
                    short_circuit = True
                    break
                    
            submission_count += Spoj.SUBMISSIONS_PER_PAGE_LIMIT
        
        LOG.debug(f"User: [{usr.user_id}] has solved: [{len(solved_questions)}] questions: [{solved_questions}]")
        return len(solved_questions)