from __future__ import unicode_literals

import json
import requests
from bs4 import BeautifulSoup

from errors import AuthenticationError

HOME_URL = 'https://mol.medicover.pl/'
LOGIN_URL = 'https://mol.medicover.pl/Users/Account/LogOn'
FORM_URL = 'https://mol.medicover.pl/api/MyVisits/SearchFreeSlotsToBook/FormModel?'
AVAILABLE_VISITS_URL = 'https://mol.medicover.pl/api/MyVisits/SearchFreeSlotsToBook?language=pl-PL'
BOOK_VISIT_URL = 'https://mol.medicover.pl/MyVisits/BookingAppointmentProcess/Confirm'


class API(object):
    def __init__(self, user, password):
        self.session = requests.Session()
        self.session.headers = {'User-Agent': 'Mozilla/5.0', 'X-Requested-With': 'XMLHttpRequest'}
        self.log_in(user, password)

    def _get_verification_token(self):
        response = self.session.get(HOME_URL)
        response.raise_for_status()
        parsed_html = BeautifulSoup(response.content, 'html.parser')
        verification_token = parsed_html.select('input[name="__RequestVerificationToken"]')[0]['value']
        return verification_token

    def log_in(self, user, password):
        payload = {
            'userNameOrEmail': user,
            'password': password,
            '__RequestVerificationToken': self._get_verification_token()
        }
        response = self.session.post(LOGIN_URL, data=payload)
        if response.status_code != 302:  # medicover backend redirects on successful login
            raise AuthenticationError

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
