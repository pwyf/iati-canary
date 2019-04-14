from flask.cli import with_appcontext
import click

from . import utils


@click.command()
@with_appcontext
def refresh_metadata():
    '''Refresh publisher metadata.'''
    utils.refresh_metadata()


@click.command()
@click.option('--days-ago', type=int, default=5)
@with_appcontext
def cleanup(days_ago):
    '''Clean expired errors from the database.'''
    utils.cleanup(days_ago)
