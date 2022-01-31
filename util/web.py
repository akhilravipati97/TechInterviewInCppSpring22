import time
from util.log import get_logger
import uuid
import requests as r

LOG = get_logger("WebRequest")

class WebRequest:
    def __init__(self, rate_limit_millis: int = 0, name: str = None) -> None:
        self.rate_limit_millis = rate_limit_millis
        self.last_request_ts_millis = 0
        self.web_request_obj_id = str(uuid.uuid4())

    def __rate_limit(self):
        req_ts_millis = int(time.time()*1000)
        if self.rate_limit_millis > 0:
            diff_millis = req_ts_millis - self.last_request_ts_millis
            LOG.debug(f"[{self.web_request_obj_id}]: Diff: {diff_millis}(ms), Rate limit: {self.rate_limit_millis}(ms)")
            if diff_millis <= self.rate_limit_millis:
                LOG.info(f"[{self.web_request_obj_id}]: Rate limit applied. Sleeping for {diff_millis}(ms).")
                time.sleep(diff_millis/1000.0) # sleep takes seconds - fractional values are allowed, so we're good
        self.last_request_ts_millis = req_ts_millis

    def get_scraper(self, url: str) -> dict:
        raise Exception("Unimplemented - get_scraper")

    def get(self, url: str, scraper: bool = False) -> dict:
        self.__rate_limit()
        if scraper:
            return self.get_scraper(url)
        return r.get(url).json()