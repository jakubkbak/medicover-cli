from __future__ import unicode_literals

import click

COMMAND_HELP = 'Available commands:\n' \
               'help - prints this message\n' \
               'fields - show available form fields\n' \
               'show {field_name} - show options for specified field\n' \
               'select {field_name} {option_index} - select option for field\n' \
               'search - search for available visits after selecting fields\n' \
               'load_more - load more results from current search\n' \
               'book {visit_index} - book visit at this index in the current results set'


class CLIFormWrapper(object):
    def __init__(self, form):
        self.form = form

    def start(self):
        click.clear()
        click.echo(COMMAND_HELP)
        while True:
            click.echo('')  # newline
            command_string = click.prompt('Enter command')
            click.clear()
            command_parts = map(unicode.strip, command_string.split(' '))
            command_name = command_parts[0]
            args_list = command_parts[1:]
            try:
                getattr(self, '_command_' + command_name)(*args_list)
            except AttributeError:
                click.echo('Unknown command')

    @staticmethod
    def _command_help():
        click.echo(COMMAND_HELP)

    def _command_fields(self):
        click.echo(self.form.fields.list())

    def _command_show(self, field_name):
        if field_name in self.form.fields:
            options_list = self.form.fields[field_name].list_options()
            click.echo(
                options_list if len(options_list) else '{} list is empty'.format(field_name)
            )
        else:
            click.echo('Unknown field name')

    def _command_select(self, field_name, option_index):
        if field_name in self.form.fields:
            field = self.form.fields[field_name]
            option_index = int(option_index)
            if option_index <= len(field.options) - 1:
                field.select(option_index)

    def _command_search(self):
        self.form.search()
        click.echo('\n'.join('{}: {}'.format(index, unicode(result)) for index, result in enumerate(self.form.results)))

    def _command_load_more(self):
        self.form.load_more()
        click.echo('\n'.join('{}: {}'.format(index, unicode(result)) for index, result in enumerate(self.form.results)))

    def _command_book(self, visit_index):
        visit_index = int(visit_index)
        try:
            visit = self.form.results[visit_index]
        except IndexError:
            click.echo('Invalid visit index')
            return
        booked_ok = visit.book()
        click.echo('Visit booked successfully' if booked_ok else 'Booking failed')
