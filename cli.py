import os

import click

from medicover import Medicover


@click.group()
@click.option('-u', default=lambda: os.environ.get('MEDICOVER_USER'), show_default=False,
              help='Your Medicover card number')
@click.option('-p', default=lambda: os.environ.get('MEDICOVER_PASSWORD'), show_default=False,
              help='Your Medicover password')
@click.pass_context
def medicover(ctx, u, p):
    ctx.obj['M'] = Medicover(user=u, password=p)


@medicover.command()
@click.pass_context
def search(ctx):
    m = ctx.obj['M']
    for field_name in m.form.fields.field_order:
        field_obj = m.form.fields[field_name]
        field_obj.list()
        value = click.prompt('Please select a value for {field_name}'.format(field_name=field_name), type=int)
        field_obj.select(value)
    m.form.search()
    while True:
        click.echo('\n'.join('{:d}: {:s}'.format(index, visit) for index, visit in enumerate(m.form.results)))
        if click.confirm('Would you like to load more results'):
            m.form.load_more()
        else:
            break
    visit_to_book_index = click.prompt('Which visit would you like to book?', type=int)
    visit = m.form.results[visit_to_book_index]
    response = visit.book()
    click.echo(response)


def main():
    return medicover(obj={})
