import csv
import sys
from datetime import date
from random import randrange

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError

from silverstrike.models import Account, Split, Transaction


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            dest='file',
            type=str,
            help='File to write to')
    def handle(self, *args, **options):
        output = sys.stdout
        if options['file']:
            try:
                output = open(options['file'], 'w')
            except FileNotFoundError:
                raise CommandError('Could not open {} for writing'.format(options['file']))

        splits = Split.objects.transfers_once().personal()
        csv_writer = csv.writer(output, delimiter=';')
        headers = [
            'account',
            'opposing_account',
            'date',
            'amount',
            'category'
            ]
        csv_writer.writerow(headers)
        for split in splits.values_list('account__name', 'opposing_account__name',
                                        'date', 'amount', 'category'):
            csv_writer.writerow(split)
        if options['file']:
            output.close()
            print('Exported transactions to {}'.format(options['file']))

    