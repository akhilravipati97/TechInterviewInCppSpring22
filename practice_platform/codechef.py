from collections import defaultdict
from os import link
from typing import Dict, List, Set, Tuple
from constants import EST_TZINFO, IST_TZINFO
from model.submission import Submission
from util.web import WebRequest
from util.log import get_logger
from contest_platform.base import ContestPlatformBase, Grading, User, Contest
from datetime import datetime, timedelta, tzinfo
import requests as r
from util.datetime import in_between_dt, to_dt_from_ts
from util.common import fail
import re
from bs4 import BeautifulSoup
from util.datetime import get_curr_dt_est

LOG = get_logger("CodechefPractice")


class CodechefPractice(ContestPlatformBase):
    """
        Codechef does not have an official API. Scraping is possible, but for things that matter
        codechef uses simple API calls to fetch data that seem to not need authentication.

        So, we'll try to use that for now.

        Rate-limiting of 1s per request will apply, to be respectful to this undocumented public api.
    """

    PLATFORM = "Codechef"
    SUBMISSIONS_URL = "https://www.codechef.com/recent/user?page={page_num}&user_handle={user_id}"
    START_PAGE_NUM = 0
    TIME_PARSE_REGEX = re.compile("([0-9]+).*(min|sec|hour)")
    WR = WebRequest(rate_limit_millis=2000)


    def name(self):
        return CodechefPractice.PLATFORM


    def __get_dt(self, time_text: str) -> datetime:
        matches = CodechefPractice.TIME_PARSE_REGEX.findall(time_text)
        if len(matches) != 0:
            curr_dt = get_curr_dt_est()
            val = int(matches[0][0])
            if "min" in time_text:
                return curr_dt + timedelta(minutes=val)
            elif "hour" in time_text:
                return curr_dt + timedelta(hours=val)
            elif "sec" in time_text:
                return curr_dt + timedelta(seconds=val)
            else:
                fail(f"Unexpected path for time parsing: [{time_text}]")
        else:
            curr_dt = datetime.strptime(time_text, "%I:%M %p %d/%m/%y")
            curr_dt.replace(tzinfo=IST_TZINFO)
            curr_dt = curr_dt.astimezone(EST_TZINFO)
            return curr_dt


    def __get_pb_ct(self, link_text: str) -> Tuple[str, str]:
        """
        Return problem_id, contest_id. The latter can be None.
        """
        parts = link_text.split("/")
        if "/problems/" not in link_text:
            fail(f"Improper link to scrape: [{link_text}], expected: '/problems/HS08TEST' or '/START24C/problems/SPECIALSTR'")
        
        if len(parts) == 3:
            return parts[-1], None
        elif len(parts) == 4:
            return parts[-1], parts[1]
        else:
            fail(f"Unexpected parts: [{parts}] for link: [{link_text}], expected: '/problems/HS08TEST' or '/START24C/problems/SPECIALSTR'")
        

    def successfull_submissions(self, gd: Grading, usr: User, usr_cts_sq: Dict[str, Set[str]] = defaultdict(set)) -> int:
        """
            The submissions url for a user returns a json that has html in it. So, we gotta parse
            that html and extract submission data.

            Complications include recent timestamps being reported as '1 sec ago, '2 min ago', '12 hours ago',
            some problems belonging to a contest and some belonging to other problem lists. We'll need to exclude
            only those problems that are part of a contest that the user submitted successfully during the contest.
        """

        short_circuit=False
        max_page_num = float('inf')
        curr_page_num = CodechefPractice.START_PAGE_NUM
        separate_practice_problems = set()
        contest_practice_problems = defaultdict(set)
        while (not short_circuit) and (curr_page_num <= max_page_num):
            submissions_url = CodechefPractice.SUBMISSIONS_URL.format(page_num=curr_page_num, user_id=usr.user_id)
            LOG.debug(f"Submission url: [{submissions_url}]")

            submission_data = CodechefPractice.WR.get(submissions_url)
            if (submission_data is None) or ("max_page" not in submission_data) or ("content" not in submission_data ):
                fail(f"Submission data not found for: [{submissions_url}]")

            if max_page_num == float("inf"):
                max_page_num = int(submission_data["max_page"])

            submission_html = submission_data["content"]
            soup = BeautifulSoup(submission_html, features="html.parser")
            tr_vals = soup.select("table[class='dataTable'] > tbody > tr")
            LOG.debug(f"num tr_vals: [{len(tr_vals)}]")

            for tr_val in tr_vals:
                td_vals = tr_val.select("td")
                LOG.debug(f"\tnum td_vals: [{len(td_vals)}]")
                time_text = td_vals[0].get("title").strip()
                link_text = td_vals[1].select_one("a").get("href").strip()
                status = td_vals[2].select_one("span").get("title").strip()
                LOG.debug(f"\t{time_text} -- {link_text} -- {status}")
                
                curr_dt = self.__get_dt(time_text)
                problem_id, contest_id = self.__get_pb_ct(link_text)

                if status == "accepted" and in_between_dt(curr_dt, gd.week_start_dt, gd.week_end_dt):
                    if contest_id is None:
                        separate_practice_problems.add(problem_id)
                    else:
                        contest_practice_problems[contest_id].add(problem_id)
                
                if curr_dt < gd.week_start_dt:
                    short_circuit = True
                    break

            curr_page_num += 1

        real_practice_problems = dict()
        for contest_id, problems in contest_practice_problems.items():
            if contest_id in usr_cts_sq:
                separate_problems = problems - usr_cts_sq[contest_id]
                LOG.debug(f"User: [{usr.user_id}] already participared in contest: [{contest_id}]. Unsolved, i.e num practice problems are: [{len(separate_problems)}] which are: [{separate_problems}]")
                real_practice_problems[contest_id] = separate_problems
            else:
                real_practice_problems[contest_id] = problems
            
        num_real_practice_problems = sum([len(problems) for problems in real_practice_problems.values()])
        num_separate_practice_problems = len(separate_practice_problems)
        LOG.debug(f"User: [{usr.user_id}] has solved real contest practice problems: [{num_real_practice_problems}] questions: [{real_practice_problems}]")
        LOG.debug(f"User: [{usr.user_id}] has solved separate practice problems: [{num_separate_practice_problems}] questions: [{separate_practice_problems}]")
        total =  num_real_practice_problems + num_separate_practice_problems
        LOG.debug(f"User: [{usr.user_id}] has total: [{total}] problems as practice")
        return total
