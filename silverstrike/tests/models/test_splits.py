from datetime import date

from django.test import TestCase

from silverstrike.models import Account, Category, RecurringTransaction, Split, Transaction
from silverstrike.tests import create_transaction


class SplitQuerySetTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='personal')
        self.savings = Account.objects.create(name='savings')
        self.foreign = Account.objects.create(name='foreign', account_type=Account.FOREIGN)

        self.transfer_transaction = create_transaction(
            'meh', self.personal, self.savings, 100, Transaction.TRANSFER, date(2017, 1, 1))
        self.deposit_transaction = create_transaction(
            'meh', self.foreign, self.personal, 100, Transaction.DEPOSIT, date(2017, 6, 1))
        self.withdraw_transaction = create_transaction(
            'meh', self.personal, self.foreign, 100, Transaction.WITHDRAW, date(2017, 12, 1))
        self.upcoming_transaction = create_transaction(
            'meh', self.personal, self.foreign, 100, Transaction.WITHDRAW, date(2200, 1, 1))

    def test_personal(self):
        queryset = Split.objects.personal()
        # we should get exactly 5 results. One for each, plus an additional for a transfer
        self.assertEquals(queryset.count(), 5)

    def test_transfers_once(self):
        queryset = Split.objects.personal().transfers_once()
        # this time we should get exactly 4.
        self.assertEquals(queryset.count(), 4)

    def test_exclude_transfers(self):
        queryset = Split.objects.personal().exclude_transfers()
        # this time we get 3. the transfer is not included
        self.assertEquals(queryset.count(), 3)

    def test_income(self):
        queryset = Split.objects.personal().income()
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset.first().transaction, self.deposit_transaction)

    def test_expense(self):
        queryset = Split.objects.personal().expense()
        self.assertEquals(queryset.count(), 2)
        queryset = queryset.past()
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset.first().transaction, self.withdraw_transaction)

    def test_date_range_includes_start(self):
        queryset = Split.objects.personal().date_range(date(2017, 6, 1), date(2017, 7, 1))
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset.first().transaction, self.deposit_transaction)

    def test_date_range_includes_end(self):
        queryset = Split.objects.personal().date_range(date(2017, 5, 1), date(2017, 6, 1))
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset.first().transaction, self.deposit_transaction)

    def test_category(self):
        category = Category.objects.create(name='category')
        for s in self.withdraw_transaction.splits.all():
            s.category = category
            s.save()
        queryset = Split.objects.personal().category(category)
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset.first().transaction, self.withdraw_transaction)

    def test_upcoming(self):
        queryset = Split.objects.personal().upcoming()
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset.first().transaction, self.upcoming_transaction)

    def test_past(self):
        queryset = Split.objects.personal().exclude_transfers().past()
        self.assertEquals(queryset.count(), 2)

    def test_recurrence(self):
        recurrence = RecurringTransaction.objects.create(
            title='some recurrence',
            amount=25,
            date=date.today(),
            src=self.personal,
            dst=self.foreign,
            recurrence=RecurringTransaction.MONTHLY,
            transaction_type=Transaction.WITHDRAW)
        self.withdraw_transaction.recurrence = recurrence
        self.withdraw_transaction.save()
        queryset = Split.objects.personal().recurrence(recurrence)
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset.first().transaction, self.withdraw_transaction)
