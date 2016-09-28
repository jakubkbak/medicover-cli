from __future__ import unicode_literals

from datetime import timedelta, datetime

from tools import camelcase_to_underscore


class SearchForm(object):
    def __init__(self, parent):
        self.parent = parent
        self.request_params = {}
        self.results = []
        self.fields = FieldSet()
        self.can_search = False
        self._parse_form_data(self.parent.api.get_form_data())

    def search(self):
        if self.can_search:
            self.results = [
                AvailableVisit(result_data, form=self) for result_data in
                self.parent.api.get_available_visits(self.request_params)
                ]

    def load_more(self):
        if len(self.results) > 0:
            self.request_params['searchForNextSince'] = self._get_next_search_since_value()
            self.search()

    def update_options(self):
        self._parse_form_data(self.parent.api.get_form_data(self.request_params))
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
        """Get the date value that medicover uses for 'load more results' request"""
        next_date = self.results[0].date + timedelta(hours=22)
        return next_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')


class FieldSet(dict):
    field_order = ['regions', 'booking_types', 'specializations', 'clinics', 'languages', 'doctors']

    def list(self):
        """
        Returns a string of all available fields on the FieldSet instance and their current values.
        """
        result = []
        for field_name in self.field_order:
            field = self[field_name]
            field_selected_text = field.selected['text'] if field.selected else ''
            result.append('{}: {}'.format(field_name, field_selected_text))
        return '\n'.join(result)


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

    def list_options(self):
        """
        Returns a string with all available option values and their indexes
        """
        return '\n'.join(
            '{:d}: {:s}'.format(index, option['text']) for index, option in enumerate(self.options)
        )

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
    date_input_format = '%Y-%m-%dT%H:%M:%S'
    date_output_format = '%d-%m-%Y %H:%M'

    def __init__(self, data, form):
        self.id = data['id']
        self.specialization = data['specializationName']
        self.clinic = data['clinicName']
        self.doctor = data['doctorName']
        self.date = datetime.strptime(data['appointmentDate'], self.date_input_format)
        self.form = form

    def __unicode__(self):
        return '{specialization}, {doctor}, {clinic}, {date}'.format(specialization=self.specialization,
                                                                     doctor=self.doctor,
                                                                     clinic=self.clinic,
                                                                     date=self.date.strftime(self.date_output_format))

    def __str__(self):
        return unicode(self).encode('utf-8')

    def book(self):
        return self.form.parent.api.book_visit(self.id)
