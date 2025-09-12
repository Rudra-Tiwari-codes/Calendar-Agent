from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

import dateparser
import pytz


def parse_natural_range(text: str, tz: str) -> Tuple[datetime, datetime]:
    settings = {"RETURN_AS_TIMEZONE_AWARE": True, "PREFER_DATES_FROM": "future"}
    parsed = dateparser.parse(text, settings=settings)
    if not parsed:
        raise ValueError("could_not_parse_time")
    if "to" in text or "-" in text:
        # crude split
        if " to " in text:
            left, right = text.split(" to ", 1)
        else:
            left, right = text.split("-", 1)
        start = dateparser.parse(left, settings=settings)
        end = dateparser.parse(right, settings=settings)
    else:
        # default 1h duration
        start = parsed
        end = parsed + dateparser.timedelta(hours=1)  # type: ignore[attr-defined]
    if not start or not end:
        raise ValueError("could_not_parse_time")
    tzinfo = pytz.timezone(tz)
    start = start.astimezone(tzinfo)
    end = end.astimezone(tzinfo)
    return start, end


