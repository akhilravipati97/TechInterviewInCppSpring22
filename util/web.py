from email import header
import time
from util.log import get_logger
import uuid
import requests as r
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from constants import CHROME_DRIVER_PATH

LOG = get_logger("WebRequest")

class WebRequest:
    def __init__(self, rate_limit_millis: int = 0, name: str = None) -> None:
        self.rate_limit_millis = rate_limit_millis
        self.last_request_ts_millis = 0
        self.web_request_obj_id = str(uuid.uuid4())

        options = Options()
        options.headless = True
        options.add_argument("--window-size=1920,1200")
        self.scraper_options = options

    def __rate_limit(self):
        req_ts_millis = int(time.time()*1000)
        if self.rate_limit_millis > 0:
            diff_millis = req_ts_millis - self.last_request_ts_millis
            LOG.debug(f"[{self.web_request_obj_id}]: Diff: {diff_millis}(ms), Rate limit: {self.rate_limit_millis}(ms)")
            if diff_millis <= self.rate_limit_millis:
                LOG.info(f"[{self.web_request_obj_id}]: Rate limit applied. Sleeping for {diff_millis}(ms).")
                time.sleep(diff_millis/1000.0) # sleep takes seconds - fractional values are allowed, so we're good
        self.last_request_ts_millis = req_ts_millis

    def scrape(self, url: str) -> webdriver.Chrome:
        LOG.debug(f"SCRAPE: [{url}]")
        self.__rate_limit()
        driver = webdriver.Chrome(options=self.scraper_options, executable_path=str(CHROME_DRIVER_PATH))
        driver.get(url)
        return driver        

    def get(self, url: str, is_json=True):
        """
        Returns dict if is_json is True, else string.
        """
        LOG.debug(f"GET: [{url}]")
        self.__rate_limit()
        resp = r.get(url)
        if is_json:
            return resp.json()
        return resp.text

    def post(self, url: str, data: dict = None, headers: dict = None):
        LOG.debug(f"POST: [{url}] with data: [{data}] and headers: [{headers}]")
        self.__rate_limit()
        if data is not None:
            if headers is not None:
                return r.post(url, data=data, headers=headers).json()
            return r.post(url, data=data).json()
        return r.post(url).json()