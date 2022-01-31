from datetime import datetime
from datetime import timedelta
import pytz
from pathlib import Path

# Timezone constants
EST_TZINFO = pytz.timezone("America/New_York")
EST_TZINFO = pytz.timezone("America/New_York")
EST_DATE_INIT = datetime.now(EST_TZINFO)
EST_TZINFO_DELTA = EST_DATE_INIT.tzinfo.utcoffset(EST_DATE_INIT)

# Main constants
TIC_WEEK_1_START_DATE = datetime(2022, 1, 15, tzinfo=EST_TZINFO)
TIC_WEEK_START_DATES = [TIC_WEEK_1_START_DATE + timedelta(days=7*i) for i in range(15)]
LOG_MODE_DEBUG = True
PROJECT_PATH = Path(".").resolve()
PROJECT_PATH_STR = str(PROJECT_PATH)