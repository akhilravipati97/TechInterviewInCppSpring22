from datetime import datetime
from datetime import timedelta
import pytz

EST_TZINFO = pytz.timezone("America/New_York")
TIC_WEEK_1_START_DATE = datetime(2022, 1, 15, tzinfo=EST_TZINFO)

TIC_WEEK_START_DATES = [TIC_WEEK_1_START_DATE + timedelta(days=7*i) for i in range(15)]