from datetime import datetime
from datetime import timedelta
import pytz
from pathlib import Path

# Timezone constants
UTC_TZINFO = pytz.timezone("UTC")
EST_TZINFO = pytz.timezone("America/New_York")
IST_TZINFO = pytz.timezone("Asia/Calcutta")
EST_DATE_INIT = datetime.now(EST_TZINFO)
EST_TZINFO_DELTA = EST_DATE_INIT.tzinfo.utcoffset(EST_DATE_INIT)

# Main constants
TIC_WEEK_1_START_DATE = datetime(2022, 1, 15, tzinfo=EST_TZINFO)
TIC_WEEK_START_DATES = [TIC_WEEK_1_START_DATE + timedelta(days=7*i) for i in range(15)]
LOG_MODE_DEBUG = True
PROJECT_PATH = Path(".").resolve()
CHROME_DRIVER_PATH = Path("./chromedriver.exe").resolve() # Please add chrome driver path here - https://chromedriver.chromium.org/downloads
PRACTICE_PROBLEM_MULTIPLIER=0.01
CONTEST_PROBLEM_MULTIPLIER=1

# Safety checks
assert((CHROME_DRIVER_PATH is not None) and type(CHROME_DRIVER_PATH) == type(Path(".")) and CHROME_DRIVER_PATH.exists())