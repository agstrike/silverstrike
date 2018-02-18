from datetime import date

from django.test import TestCase

from silverstrike.models import Account, Transaction
from silverstrike.tests import create_transaction


class TransactionQuerySetTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='personal')
        self.foreign = Account.objects.create(name='foreign', account_type=Account.FOREIGN)

    def test_last_10_returns_at_most_10(self):
        for i in range(1, 32):
            create_transaction('meh', self.foreign, self.personal, 50, Transaction.DEPOSIT,
                               date=date(2018, 1, i))
        queryset = Transaction.objects.last_10()
        self.assertEquals(queryset.count(), 10)
        # they have to be the last ones
        for t in queryset:
            self.assertGreater(t.date.day, 20)

    def test_last_10_returns_something(self):
        create_transaction('meh', self.foreign, self.personal, 50, Transaction.DEPOSIT,
                           date=date(2018, 1, 1))
        self.assertEquals(Transaction.objects.last_10().count(), 1)
