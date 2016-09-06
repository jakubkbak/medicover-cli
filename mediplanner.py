import json
import os
import re

import requests
from bs4 import BeautifulSoup

HOME_URL = 'https://mol.medicover.pl/'
LOGIN_URL = 'https://mol.medicover.pl/Users/Account/LogOn'
FORM_URL = 'https://mol.medicover.pl/api/MyVisits/SearchFreeSlotsToBook/FormModel?'


def camelcase_to_underscore(val):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', val)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class MedicoverSession(object):
    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'Mozilla/5.0', 'X-Requested-With': 'XMLHttpRequest'}
        self.log_in()

    def get_verification_token(self):
        response = self.session.get(HOME_URL)
        response.raise_for_status()
        parsed_html = BeautifulSoup(response.content, 'html.parser')
        verification_token = parsed_html.select('input[name="__RequestVerificationToken"]')[0]['value']
        return verification_token

    def log_in(self):
        payload = {
            'userNameOrEmail': os.environ.get('MEDICOVER_USER'),
            'password': os.environ.get('MEDICOVER_PASSWORD'),
            '__RequestVerificationToken': self.get_verification_token()
        }
        response = self.session.post(LOGIN_URL, data=payload)
        response.raise_for_status()

    def get_form_data(self, params=None):
        response = self.session.get(FORM_URL, params=params)
        return json.loads(response.content)


class MedicoverForm(object):
    def __init__(self):
        self.medicover_session = MedicoverSession()
        self.options = self.parse_options(self.medicover_session.get_form_data())

    def parse_options(self, data):
        result = OptionSet()
        for option_name, values in data.items():
            if option_name.startswith('available'):
                result[camelcase_to_underscore(option_name)] = OptionSet(values)
        return result


class OptionSet(dict):
    
    def __init__(self, data=None):
        data = [(option['text'], Option(name=option['text'], value=option['id'], option_set=self)) for option in data]
        super(OptionSet, self).__init__(data)

    def __getattr__(self, name):
        if isinstance(self[name], OptionSet):
            print self[name].keys()
        else:
            return self[name]


class Option(object):

    def __init__(self, name, value, option_set):
        self.name = name
        self.value = value
        self.option_set = option_set
