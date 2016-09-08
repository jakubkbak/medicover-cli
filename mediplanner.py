from __future__ import unicode_literals

import json
import os
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup

from errors import ConfigurationError


HOME_URL = 'https://mol.medicover.pl/'
LOGIN_URL = 'https://mol.medicover.pl/Users/Account/LogOn'
FORM_URL = 'https://mol.medicover.pl/api/MyVisits/SearchFreeSlotsToBook/FormModel?'
AVAILABLE_VISITS_URL = 'https://mol.medicover.pl/api/MyVisits/SearchFreeSlotsToBook?language=pl-PL'
BOOK_VISIT_URL = 'https://mol.medicover.pl/MyVisits/BookingAppointmentProcess/Confirm'

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


class API(object):
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
        try:
            user = os.environ['MEDICOVER_USER']
            password = os.environ['MEDICOVER_PASSWORD']
        except KeyError as e:
            raise ConfigurationError('{:s} not found in env variables'.format(e.args[0]))
        payload = {
            'userNameOrEmail': user,
            'password': password,
            '__RequestVerificationToken': self.get_verification_token()
        }
        response = self.session.post(LOGIN_URL, data=payload)
        response.raise_for_status()

    def get_form_data(self, params=None):
        params = params or {}
        response = self.session.get(FORM_URL, params=params)
        return json.loads(response.content)

    def get_available_visits(self, data=None):
        data = data or {}
        response = self.session.post(AVAILABLE_VISITS_URL, data=data)
        available_visits = response.json()['items']
        return available_visits

    def book_visit(self, visit_id):
        confirmation_page = self.session.get(BOOK_VISIT_URL, params={'id': visit_id})
        parsed_html = BeautifulSoup(confirmation_page.content, 'html.parser')
        form = parsed_html.find('form', {'action': '/MyVisits/BookingAppointmentProcess/Confirm'})
        input_tags = form.find_all('input')
        post_data = {input_tag['name']: input_tag['value'] for input_tag in input_tags}
        response = self.session.post(BOOK_VISIT_URL, data=post_data)
        return response.ok


class Form(object):
    def __init__(self):
        self.api = API()
        self.request_params = {}
        self.results = []
        self.can_search = False
        self.fields = FieldSet()
        self.parse_form_data(self.api.get_form_data())

    def parse_form_data(self, data):
        for select_name, option_list in data.items():
            if select_name.startswith('available'):
                underscore_name = camelcase_to_underscore(select_name.lstrip('available_'))
                self.fields[underscore_name] = OptionList(
                    name=underscore_name,
                    form=self,
                    seq=[option for option in option_list if option['id'] >= 0]
                )
        self.can_search = data['canSearch']

    def update_options(self):
        self.parse_form_data(self.api.get_form_data(self.request_params))

    def search(self):
        if self.can_search:
            self.results = [
                Appointment(result_data, form=self) for result_data in
                self.api.get_available_visits(self.request_params)
                ]


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
        return '\n'.join(
            '{:d}: {:s}'.format(index, option['text']) for index, option in enumerate(self)
        ).encode('utf-8')

    def select(self, index):
        option_url_param_name = OPTION_TO_PARAM_MAP[self.name]
        self.form.request_params[option_url_param_name] = self[index]['id']
        self.form.update_options()


class Appointment(object):
    def __init__(self, data, form):
        self.id = data['id']
        self.doctor = data['doctorName']
        self.specialization = data['specializationName']
        self.date = datetime.strptime(data['appointmentDate'], '%Y-%m-%dT%H:%M:%S')
        self.form = form

    def book(self):
        return self.form.api.book_visit(self.id)
