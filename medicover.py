from __future__ import unicode_literals

from api import API
from search_form import SearchForm


class Medicover(object):
    def __init__(self, user, password):
        self.api = API(user, password)
        self.form = SearchForm(parent=self)
