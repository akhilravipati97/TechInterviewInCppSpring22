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

LOG = get_logger("Dmoj")


class Dmoj(ContestPlatformBase):
    """
        Dmoj has an official API. They say they need API tokens, but for now public access is working just fine.

        Rate-limiting of 1s per request will apply. Dmoj will strictly enforce 90 requests/minute with a 3-day ban 
        for offenders.
    """

    PLATFORM = "Dmoj"

    # Only rated contests
    CONTESTS_URL = "https://dmoj.ca/api/v2/contests?is_rated=True"
    SUBMISSIONS_URL = "https://dmoj.ca/api/v2/contest/{contest_id}"
    
    WR = WebRequest(rate_limit_millis=1000)
    POINTS_CACHE = dict()


    def name(self):
        return Dmoj.PLATFORM


    def all_contests(self, gd: Grading) -> List[Contest]:
        """
            Dmoj's API shows all contests at once. We'll need to filter the list on our end.

            NOTE: Because it is highly unlikely to change, for a grading week, we should probably also cache them.

            Return a list of contests.

            Sample json:
            {
                "api_version": "2.0",
                "method": "get",
                "fetched": "2022-02-02T22:32:25.388875+00:00",
                "data": {
                    "current_object_count": 121,
                    "objects_per_page": 1000,
                    "page_index": 1,
                    "has_more": false,
                    "objects": [
                    {
                        "key": "dmopc14c2",
                        "name": "DMOPC '14 November Contest",
                        "start_time": "2014-11-18T20:30:00+00:00",
                        "end_time": "2014-11-18T23:30:00+00:00",
                        "time_limit": null,
                        "is_rated": true,
                        "rate_all": false,
                        "tags": [
                        "dmopc"
                        ]
                    },
                    ...
        """
        
        contests = Dmoj.WR.get(Dmoj.CONTESTS_URL)
        if (contests is None) or (contests["data"] is None) or (len(contests["data"]["objects"]) == 0):
            fail(f"No contests found", LOG)

        contests = contests["data"]["objects"]

        # Dmoj contests are returned in ascending order of start time. Reversing it.
        contests = contests[::-1]

        curr_contests = []
        for contest in contests:
            curr_dt = datetime.fromisoformat(contest["start_time"])
            if in_between_dt(curr_dt, gd.week_start_dt, gd.week_end_dt):
                curr_contests.append({**contest, "startDatetime": curr_dt})

            if curr_dt < gd.week_start_dt:
                LOG.debug(f"Breaking because contest: [{contest['key'] + ' -- ' + contest['name']}] started at: [{curr_dt}] and is older than: [{gd.week_start_dt}]")
                break
                
        LOG.debug(f"Contests: {[contest['key'] + ' -- ' + contest['name'] for contest in curr_contests]}")
        return [Contest(str(contest['key'])) for contest in curr_contests]


    def __get_points(self, usr: User, ct: Contest) -> Submission:
        usr_handle = usr.handle(self.name())
        if usr_handle not in Dmoj.POINTS_CACHE[ct.contest_id]:
            LOG.info(f"user: [{usr_handle}] not found in points cache for contest: [{ct.contest_id}]")
            return Submission()

        val = Dmoj.POINTS_CACHE[ct.contest_id][usr_handle]
        if val["is_disqualified"]:
            LOG.warn(f"user: [{usr_handle}] is disqualified in [{ct.contest_id}], returning 0 points")
            return Submission()

        LOG.debug(f"user: [{usr_handle}] in contest: [{ct.contest_id}] solved these questions: [{val['solved_questions']}]")
        if len(val["partially_solved_questions"]) > 0:
            LOG.warn(f"user: [{usr_handle}] in contest: [{ct.contest_id}] has a partially solved questions: [{val['partially_solved_questions']}], ignoring it for now.")
        return Submission(set(val['solved_questions']))
        

    def successful_submissions(self, gd: Grading, ct: Contest, usr: User) -> Submission:
        """
            Dmoj contest url gives out every bit of information for that contest including rankings and submissions.
            So, we can directly hit that endpoint and perform all calculations

            NOTE: As this contest information will repeat for each user, we can cache the results/processed data.
            We can also make this part of a pre-processing step as soon as a grading week ends. For now, going with the
            cache route.

            NOTE: HAVEN"T FULLY THOUGHT ABOUT PARTIAL POINTS PROBLEMS AND HOW TO GRADE THEM. For now it'll just get logged.

            Sample json:
            {
                "api_version": "2.0",
                "method": "get",
                "fetched": "2022-02-02T22:51:44.940832+00:00",
                "data": {
                    "object": {
                        "key": "aac5",
                        "name": "An Animal Contest 5",
                        "start_time": "2022-01-22T05:00:00+00:00",
                        "end_time": "2022-01-25T05:00:00+00:00",
                        "time_limit": 10800,
                        "is_rated": true,
                        "rate_all": true,
                        "has_rating": true,
                        "rating_floor": null,
                        "rating_ceiling": 2399,
                        "hidden_scoreboard": true,
                        "scoreboard_visibility": "P",
                        "is_organization_private": false,
                        "organizations": [],
                        "is_private": false,
                        "tags": [],
                        "format": {
                            "name": "atcoder",
                            "config": {
                            "penalty": 0
                            }   
                        },
                        "problems": [
                            {
                                "points": 100,
                                "partial": true,
                                "is_pretested": false,
                                "max_submissions": 50,
                                "label": "1",
                                "name": "An Animal Contest 5 P1 - Bamboo Cookies",
                                "code": "aac5p1"
                            },
                            ....

                            ....
                        ],
                        "rankings": [
                            {
                                "user": "d",
                                "start_time": "2022-01-23T21:14:22+00:00",
                                "end_time": "2022-01-24T00:14:22+00:00",
                                "score": 600,
                                "cumulative_time": 10186,
                                "tiebreaker": 0,
                                "old_rating": 2953,
                                "new_rating": null,
                                "is_disqualified": false,
                                "solutions": [
                                    {
                                    "time": 100,
                                    "points": 100,
                                    "penalty": 0
                                    },
                                    ...
                                ]
                            },
                            ...
        """

        # Returned cached values if present
        if ct.contest_id in Dmoj.POINTS_CACHE:
            return self.__get_points(usr, ct)

        # Process and cache results
        submissions_url = Dmoj.SUBMISSIONS_URL.format(contest_id=ct.contest_id)
        LOG.debug(f"Fetching contest info for: [{submissions_url}]")

        contest_data = Dmoj.WR.get(submissions_url)
        if (contest_data is None) or ("data" not in contest_data) or ("object" not in contest_data["data"]) or ("problems" not in contest_data["data"]["object"]) or ("rankings" not in contest_data["data"]["object"]):
            fail(f"No submission data found for: [{ct.contest_id}] at: {[submissions_url]}", LOG)

        problems = contest_data["data"]["object"]["problems"]
        rankings = contest_data["data"]["object"]["rankings"]

        cache_dict = dict()
        for participant in rankings:
            user_name = participant["user"]
            disq = participant["is_disqualified"]                
            solved_questions = []
            partially_solved_questions = []

            for i, solution in enumerate(participant["solutions"]):
                # LOG.debug(f"usr: {user_name} solution: {solution}")
                if solution is None:
                    continue
                problem_name = problems[i]["code"] + " -- " + problems[i]["name"]
                if solution["points"] == problems[i]["points"]:
                    solved_questions.append(problem_name)
                elif solution["points"] > 0:
                    partially_solved_questions.append({"problem": problem_name, "points_obtained": solution["points"], "points_total": problems[i]["points"]})

            
            cache_dict[user_name] = {"solved_questions": solved_questions, "partially_solved_questions": partially_solved_questions, "is_disqualified": disq}

        # To prevent any failures mid-way from leaving behind a partially formed cache
        Dmoj.POINTS_CACHE[ct.contest_id] = cache_dict
        LOG.info(f"Cached points data for contest: [{ct.contest_id}]")

        return self.__get_points(usr, ct)

        
