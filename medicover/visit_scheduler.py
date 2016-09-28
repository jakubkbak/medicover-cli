from __future__ import unicode_literals

from datetime import datetime

from tools import time_string_to_tuple, weekday_to_int


class VisitPreference(object):
    DATE_FORMAT = '%d.%m.%Y'

    def __init__(self, search_params, time_from=None, time_to=None, date_from=None, date_to=None, weekday=None):
        self.search_params = search_params
        self.time_from = time_string_to_tuple(time_from) if time_from else None
        self.time_to = time_string_to_tuple(time_to) if time_to else None
        self.date_from = datetime.strptime(date_from, self.DATE_FORMAT) if date_from else None
        self.date_to = datetime.strptime(date_to, self.DATE_FORMAT) if date_to else None
        self.weekday = weekday_to_int(weekday) if weekday else None

    def check_if_visit_matches(self, available_visit):
        if self.weekday and self.weekday != available_visit.date.weekday():
            return False
        if self.time_from and self.time_from >= (available_visit.date.hour, available_visit.date.minute):
            return False
        if self.time_to and self.time_to <= (available_visit.date.hour, available_visit.date.minute):
            return False
        if self.date_from and self.date_from > available_visit.date:
            return False
        if self.date_to and self.date_to < available_visit.data:
            return False
        return True
