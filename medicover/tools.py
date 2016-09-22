from __future__ import unicode_literals

import re


def camelcase_to_underscore(val):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', val)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def time_string_to_tuple(string):
    """
    :param string: time in the format 'hour:minute'
    :return: tuple of ints: (hour, minute)
    """
    return tuple(int(time_part) for time_part in string.split(':'))


def weekday_to_int(string):
    """
    :param string: english name of the weekday e.g. 'monday'
    :return: int representing the weekday just like date.weekday()
    """
    try:
        return ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday').index(string.lower())
    except ValueError:
        raise Exception('Incorrect weekday name')
