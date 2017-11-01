from django.core.management.base import BaseCommand, CommandError

from silverstrike.lib import import_firefly


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            'file',
            type=str,
            help='File to import')

    def handle(self, *args, **options):
        try:
            import_firefly(options['file'])
        except FileNotFoundError:
            raise CommandError('Could not open {} for writing'.format(options['file']))
        else:
            print('Imported transactions from {}'.format(options['file']))
