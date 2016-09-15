from __future__ import unicode_literals

from datetime import timedelta, datetime

from api import API
from tools import camelcase_to_underscore


class SearchForm(object):
    def __init__(self):
        self.api = API()
        self.request_params = {}
        self.results = []
        self.fields = FieldSet()
        self.can_search = False
        self._parse_form_data(self.api.get_form_data())

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

    def update_options(self):
        self._parse_form_data(self.api.get_form_data(self.request_params))
        # do not check on first update (request_params still empty)
        if self.request_params:
            self._check_if_selected_options_still_valid()

    def _parse_form_data(self, data):
        for field_name, option_list in data.items():
            if field_name.startswith('available'):
                underscore_name = camelcase_to_underscore(field_name.lstrip('available_'))
                if underscore_name in self.fields:
                    del self.fields[underscore_name].options[:]
                    self.fields[underscore_name].options.extend(option_list)
                else:
                    self.fields[underscore_name] = Field(
                        form=self,
                        name=underscore_name,
                        options_list=option_list
                    )
        self.can_search = data['canSearch']

    def _check_if_selected_options_still_valid(self):
        for field in self.fields.values():
            if field.selected and field.selected not in field.options:
                print 'Previously selected value for "{field}" ' \
                      'is not available with current selection'.format(field=field.name)

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


class Field(object):

    OPTION_TO_PARAM_MAP = {
        'regions': 'regionId',
        'clinics': 'clinicId',
        'booking_types': 'bookingTypeId',
        'languages': 'languageId',
        'diagnostic_procedures': 'diagnosticProcedureId',
        'doctors': 'doctorId',
        'specializations': 'specializationId'
    }

    def __init__(self, form, name, options_list):
        self.form = form
        self.name = name
        self.selected = None
        # filter out interface options like 'Choose doctor'
        self.options = [option for option in options_list if option['id'] >= 0]

    def list(self):
        """
        Prints all available option values as an enumerated list.
        """
        print '\n'.join(
            '{:d}: {:s}'.format(index, option['text']) for index, option in enumerate(self.options)
        ).encode('utf-8')

    def select(self, index):
        """
        Selects the option at the specified index and updates other fields based on the return value from the server.

        Example:
            form = SearchForm()
            form.fields.clinics.select(14)

            This narrows down form.fields.doctors to only those who work in selected clinic.
        """
        selected_option = self.options[index]
        option_url_param_name = self.OPTION_TO_PARAM_MAP[self.name]
        selected_option_id = selected_option['id']
        self.form.request_params[option_url_param_name] = selected_option_id
        self.selected = selected_option
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
