from __future__ import unicode_literals

import click

COMMAND_HELP = 'Available commands:\n' \
               'fields - show available form fields\n' \
               'show {field_name} - show options for specified field\n' \
               'select {field_name} {option_index} - select option for field'


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
            command_name = command_parts.pop(0)
            args_dict = dict(zip(('field_name', 'option_index'), command_parts))
            try:
                getattr(self, '_command_' + command_name)(**args_dict)
            except AttributeError:
                click.echo('Unknown command')

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
        option_index = int(option_index)
        if field_name in self.form.fields:
            field = self.form.fields[field_name]
            if option_index <= len(field.options) - 1:
                field.select(option_index)
