import click


class CLIFormWrapper(object):

    def __init__(self, form):
        self.fields = [(field_name, form.fields[field_name]) for field_name in form.fields.field_order]
        self.current_field_index = 0
        self.current_field_name, self.current_field = self.fields[self.current_field_index]

    def start(self):
        while self.current_field_index < len(self.fields):
            self.list_options()
            value = self.prompt_for_value()
            if value >= 0:
                self.select_value(value)
                self.next_field()
            else:
                self.previous_field()

    def list_options(self):
        click.echo(self.current_field.list())

    def prompt_for_value(self):
        return click.prompt('Please provide a value for {}'.format(self.current_field_name), type=int)

    def next_field(self):  # TODO: IndexError
        self.current_field_index += 1
        self.current_field_name, self.current_field = self.fields[self.current_field_index]

    def previous_field(self):
        self.current_field_index -= 1
        self.current_field_name, self.current_field = self.fields[self.current_field_index]

    def select_value(self, value):
        self.current_field.select(value)
