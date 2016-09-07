from __future__ import unicode_literals

import json
import os
import re

import requests
from bs4 import BeautifulSoup

HOME_URL = 'https://mol.medicover.pl/'
LOGIN_URL = 'https://mol.medicover.pl/Users/Account/LogOn'
FORM_URL = 'https://mol.medicover.pl/api/MyVisits/SearchFreeSlotsToBook/FormModel?'

OPTION_TO_PARAM_MAP = {
    'regions': 'regionId',
    'clinics': 'clinicId',
    'booking_types': 'bookingTypeId',
    'languages': 'languageId',
    'diagnostic_procedures': 'diagnosticProcedureId',
    'doctors': 'doctorId',
    'specializations': 'specializationId'
}


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
        params = params or {}
        response = self.session.get(FORM_URL, params=params)
        return json.loads(response.content)


class MedicoverForm(object):
    def __init__(self):
        self.medicover_session = MedicoverSession()
        self.request_params = {}
        self.field_set = FieldSet(form=self)
        self.parse_form_data(self.medicover_session.get_form_data())

    def parse_form_data(self, data):
        for select_name, option_list in data.items():
            if select_name.startswith('available'):
                underscore_name = camelcase_to_underscore(select_name.lstrip('available_'))
                self.field_set[underscore_name] = OptionList(underscore_name, self, [option for option in option_list if option['id'] >= 0])

    def update_options(self):
        self.parse_form_data(self.medicover_session.get_form_data(self.request_params))


class CustomDictMixin(object):
    def __getattr__(self, name):
        return self[name]

    def __repr__(self):
        return '\n'.join(key_name for key_name in self.keys()).encode('utf-8')


class FieldSet(CustomDictMixin, dict):
    pass


class OptionList(list):

    def __init__(self, name, form, seq=()):
        self.name = name
        self.form = form
        super(OptionList, self).__init__(seq)

    def __repr__(self):
        return '\n'.join('{:d}: {:s}'.format(index, option['text']) for index, option in enumerate(self)).encode('utf-8')

    def select(self, index):
        option_url_param_name = OPTION_TO_PARAM_MAP[self.name]
        self.form.request_params[option_url_param_name] = self[index]['id']
