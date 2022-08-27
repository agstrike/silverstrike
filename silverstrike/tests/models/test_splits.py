from datetime import date

from django.test import TestCase
from django.urls import reverse

from silverstrike.models import (Account, AccountType, Category,
                                 RecurringTransaction, Split, Transaction)
from silverstrike.tests import create_transaction


class SplitQuerySetTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='personal')
        self.savings = Account.objects.create(name='savings')
        self.foreign = Account.objects.create(
            name='foreign',
            account_type=AccountType.FOREIGN)

        self.transfer_transaction = create_transaction(
            'transfer', self.personal, self.savings, 100, Transaction.TRANSFER, date(2017, 1, 1))
        self.deposit_transaction = create_transaction(
            'deposit', self.foreign, self.personal, 100, Transaction.DEPOSIT, date(2017, 6, 1))
        self.withdraw_transaction = create_transaction(
            'withdraw', self.personal, self.foreign, 100, Transaction.WITHDRAW, date(2017, 12, 1))
        self.upcoming_transaction = create_transaction(
            'upcoming', self.personal, self.foreign, 100, Transaction.WITHDRAW, date(2200, 1, 1))

    def test_personal(self):
        queryset = Split.objects.personal()
        # we should get exactly 5 results. One for each, plus an additional for a transfer
        self.assertEqual(queryset.count(), 5)

    def test_transfers_once(self):
        queryset = Split.objects.personal().transfers_once()
        # this time we should get exactly 4.
        self.assertEqual(queryset.count(), 4)

    def test_exclude_transfers(self):
        queryset = Split.objects.personal().exclude_transfers()
        # this time we get 3. the transfer is not included
        self.assertEqual(queryset.count(), 3)

    def test_income(self):
        queryset = Split.objects.personal().income()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.deposit_transaction)

    def test_expense(self):
        queryset = Split.objects.personal().expense()
        self.assertEqual(queryset.count(), 2)
        queryset = queryset.past()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.withdraw_transaction)

    def test_date_range_includes_start(self):
        queryset = Split.objects.personal().date_range(date(2017, 6, 1), date(2017, 7, 1))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.deposit_transaction)

    def test_date_range_includes_end(self):
        queryset = Split.objects.personal().date_range(date(2017, 5, 1), date(2017, 6, 1))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.deposit_transaction)

    def test_category(self):
        category = Category.objects.create(name='category')
        for s in self.withdraw_transaction.splits.all():
            s.category = category
            s.save()
        queryset = Split.objects.personal().category(category)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.withdraw_transaction)

    def test_upcoming(self):
        queryset = Split.objects.personal().upcoming()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.upcoming_transaction)

    def test_past(self):
        queryset = Split.objects.personal().exclude_transfers().past()
        self.assertEqual(queryset.count(), 2)

    def test_recurrence(self):
        recurrence = RecurringTransaction.objects.create(
            title='some recurrence',
            amount=25,
            date=date.today(),
            src=self.personal,
            dst=self.foreign,
            interval=RecurringTransaction.MONTHLY,
            transaction_type=Transaction.WITHDRAW)
        self.withdraw_transaction.recurrence = recurrence
        self.withdraw_transaction.save()
        queryset = Split.objects.personal().recurrence(recurrence)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.withdraw_transaction)


class SplitModelTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='personal')
        self.savings = Account.objects.create(name='savings')
        self.foreign = Account.objects.create(
            name='foreign',
            account_type=AccountType.FOREIGN)

    def test_split_str_method(self):
        transaction = create_transaction('meh', self.foreign, self.personal,
                                         100, Transaction.DEPOSIT)
        split = transaction.splits.first()
        self.assertEqual(str(split), split.title)

    def test_split_absolute_url(self):
        account = Account.objects.create(name="foo")
        account.set_initial_balance(10)
        split = Split.objects.first()
        self.assertEqual(split.get_absolute_url(), reverse('transaction_detail',
                                                           args=[split.transaction.id]))
