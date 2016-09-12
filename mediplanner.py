from __future__ import unicode_literals

import json
import os
import re
import requests
from datetime import datetime, timedelta
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


class Medicover(object):
    def __init__(self):
        self.form = SearchForm()


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

    def get_form_data(self, request_params=None):
        if request_params is None:
            request_params = {}
        response = self.session.get(FORM_URL, params=request_params)
        return json.loads(response.content)

    def get_available_visits(self, request_data=None):
        if request_data is None:
            request_data = {}
        response = self.session.post(AVAILABLE_VISITS_URL, data=request_data)
        available_visits = response.json()['items']
        return available_visits

    def book_visit(self, visit_id):
        # Parsing HTML is required to get the verification token and visit data from the form tag
        confirmation_page = self.session.get(BOOK_VISIT_URL, params={'id': visit_id})
        parsed_html = BeautifulSoup(confirmation_page.content, 'html.parser')
        form = parsed_html.find('form', {'action': '/MyVisits/BookingAppointmentProcess/Confirm'})
        input_tags = form.find_all('input')
        post_data = {input_tag['name']: input_tag['value'] for input_tag in input_tags}
        response = self.session.post(BOOK_VISIT_URL, data=post_data)
        return response.ok


class SearchForm(object):
    def __init__(self):
        self.api = API()
        self.request_params = {}
        self.results = []
        self.fields = FieldSet()
        self.can_search = False
        self.parse_form_data(self.api.get_form_data())

    def parse_form_data(self, data):
        for field_name, option_list in data.items():
            if field_name.startswith('available'):
                underscore_name = camelcase_to_underscore(field_name.lstrip('available_'))
                self.fields[underscore_name] = Options(
                    field_name=underscore_name,
                    form=self,
                    seq=[option for option in option_list if option['id'] >= 0]
                )
        self.can_search = data['canSearch']

    def update_options(self):
        self.parse_form_data(self.api.get_form_data(self.request_params))

    def search(self):
        if self.can_search:
            self.results = [
                AvailableVisit(result_data, form=self) for result_data in
                self.api.get_available_visits(self.request_params)
                ]

    def load_more(self):
        if len(self.results) > 0:
            self.request_params['searchForNextSince'] = self._get_next_search_since_value()
            self.search()

    def _get_next_search_since_value(self):
        next_date = self.results[0].date + timedelta(hours=22)
        return next_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')


class FieldSet(dict):
    def __getattr__(self, name):
        """
        Performs dict lookup using the attribute name as the dict key.
        """
        return self[name]

    def list(self):
        """
        Lists all available fields on the FieldSet instance.
        """
        print '\n'.join(key_name for key_name in self.keys()).encode('utf-8')


class Options(list):
    def __init__(self, field_name, form, seq=()):
        self.field_name = field_name
        self.form = form
        super(Options, self).__init__(seq)

    def list(self):
        """
        Prints all available option values as an enumerated list.
        """
        print '\n'.join(
            '{:d}: {:s}'.format(index, option['text']) for index, option in enumerate(self)
        ).encode('utf-8')

    def select(self, index):
        """
        Selects the option at the specified index and updates other fields based on the return value from the server.

        Example:
            form = SearchForm()
            form.fields.clinics.select(14)

            This narrows down form.fields.doctors to only those who work in selected clinic.
        """
        option_url_param_name = OPTION_TO_PARAM_MAP[self.field_name]
        self.form.request_params[option_url_param_name] = self[index]['id']
        self.form.update_options()


class AvailableVisit(object):
    def __init__(self, data, form):
        self.id = data['id']
        self.doctor = data['doctorName']
        self.specialization = data['specializationName']
        self.date = datetime.strptime(data['appointmentDate'], '%Y-%m-%dT%H:%M:%S')
        self.form = form

    def book(self):
        return self.form.api.book_visit(self.id)


class VisitPreference(object):
    def __init__(self, search_params, hour_from=None, hour_to=None, date_from=None, date_to=None, weekday=None):
        self.search_params = search_params
        self.hour_from = hour_from
        self.hour_to = hour_to
        self.date_from = date_from
        self.date_to = date_to
        self.weekday = weekday

    def search(self):
        api = API()
        results = [
            AvailableVisit(result_data, form=self) for result_data in
            api.get_available_visits(self.search_params)
            ]

    def check_if_visit_matches(self, available_visit):
        if self.weekday and self.weekday != available_visit.date.isoweekday():
            return False
        if self.hour_from and self.hour_from > available_visit.date.hour:
            return False
        if self.hour_to and self.hour_to < available_visit.date.hour:
            return False
        if self.date_from and self.date_from > available_visit.date:
            return False
        if self.date_to and self.date_to < available_visit.data:
            return False
        return True
