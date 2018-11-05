from datetime import date

from django.test import TestCase
from django.urls import reverse

from silverstrike.models import Account, Category, RecurringTransaction, Split, Transaction
from silverstrike.tests import create_transaction


class SplitQuerySetTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='personal')
        self.savings = Account.objects.create(name='savings')
        self.foreign = Account.objects.create(name='foreign', account_type=Account.FOREIGN)

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
        queryset = Split.objects.transfers_once()
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
        recurrence = create_recurring_transaction('recurrence', 
            self.personal, self.foreign, 100, RecurringTransaction.WITHDRAW, 
            RecurringTransaction.MONTHLY)
        self.withdraw_transaction.recurrence = recurrence
        self.withdraw_transaction.save()
        queryset = Split.objects.personal().recurrence(recurrence)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.withdraw_transaction)


class SplitModelTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='personal')
        self.savings = Account.objects.create(name='savings')
        self.foreign = Account.objects.create(name='foreign', account_type=Account.FOREIGN)

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

    def test_is_transfer(self):
        transaction = create_transaction('meh', self.personal, self.savings,
                                         100, Transaction.TRANSFER)
        for split in transaction.splits.all():
            self.assertTrue(split.is_transfer)
            self.assertFalse(split.is_withdraw)
            self.assertFalse(split.is_deposit)
            self.assertFalse(split.is_system)

    def test_is_withdraw(self):
        transaction = create_transaction('meh', self.personal, self.foreign,
                                         100, Transaction.WITHDRAW)
        for split in transaction.splits.all():
            self.assertTrue(split.is_withdraw)
            self.assertFalse(split.is_transfer)
            self.assertFalse(split.is_deposit)
            self.assertFalse(split.is_system)

    def test_is_deposit(self):
        transaction = create_transaction('meh', self.foreign, self.personal,
                                         100, Transaction.DEPOSIT)
        for split in transaction.splits.all():
            self.assertTrue(split.is_deposit)
            self.assertFalse(split.is_withdraw)
            self.assertFalse(split.is_transfer)
            self.assertFalse(split.is_system)

    def test_is_system(self):
        self.personal.set_initial_balance(100)
        transaction = Transaction.objects.first()
        for split in transaction.splits.all():
            self.assertTrue(split.is_system)
            self.assertFalse(split.is_withdraw)
            self.assertFalse(split.is_deposit)
            self.assertFalse(split.is_transfer)

    def test_is_system(self):
        self.personal.set_initial_balance(100)
        transaction = Transaction.objects.first()
        self.assertFalse(transaction.is_transfer)
        self.assertFalse(transaction.is_withdraw)
        self.assertFalse(transaction.is_deposit)
        self.assertTrue(transaction.is_system)