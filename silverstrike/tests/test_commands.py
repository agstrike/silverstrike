from django.core.management import call_command
from django.test import TestCase

from silverstrike.models import Transaction


class CommandsTestCase(TestCase):
    def test_createtestdata(self):
        args = []
        opts = {}
        Transaction.objects.create(title='meh', transaction_type=1)
        call_command('createtestdata', *args, **opts)
