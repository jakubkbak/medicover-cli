import click


@click.command()
@click.option('--region')
def hello(region):
    print region
