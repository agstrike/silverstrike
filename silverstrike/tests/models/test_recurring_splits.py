from datetime import date

from django.test import TestCase
from django.urls import reverse

from silverstrike.models import (Account, Category, RecurringSplit,
                                 RecurringTransaction)
from silverstrike.tests import create_recurring_transaction


class RecurringSplitQuerySetTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='personal')
        self.savings = Account.objects.create(name='savings')
        self.foreign = Account.objects.create(name='foreign', account_type=Account.FOREIGN)

        self.transfer_transaction = create_recurring_transaction(
            'transfer', self.personal, self.savings, 100,
            RecurringTransaction.TRANSFER, RecurringTransaction.MONTHLY,
            date=date(2017, 1, 1))
        self.deposit_transaction = create_recurring_transaction(
            'deposit', self.foreign, self.personal, 100,
            RecurringTransaction.DEPOSIT, RecurringTransaction.MONTHLY,
            date=date(2017, 6, 1))
        self.withdraw_transaction = create_recurring_transaction(
            'withdraw', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.MONTHLY,
            date=date(2017, 12, 1))
        self.upcoming_transaction = create_recurring_transaction(
            'upcoming', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.MONTHLY,
            date=date(2200, 1, 1))

    def test_not_disabled(self):
        create_recurring_transaction('disabled', self.personal, self.foreign,
                                     100, RecurringTransaction.WITHDRAW,
                                     RecurringTransaction.DISABLED)
        create_recurring_transaction('daily', self.personal, self.foreign, 100,
                                     RecurringTransaction.WITHDRAW, RecurringTransaction.DAILY)
        create_recurring_transaction('weekly', self.personal, self.foreign, 100,
                                     RecurringTransaction.WITHDRAW, RecurringTransaction.WEEKLY)
        create_recurring_transaction('monthly', self.personal, self.foreign,
                                     100, RecurringTransaction.WITHDRAW,
                                     RecurringTransaction.MONTHLY)
        create_recurring_transaction('annually', self.personal, self.foreign,
                                     100, RecurringTransaction.WITHDRAW,
                                     RecurringTransaction.ANNUALLY)
        queryset = RecurringSplit.objects.not_disabled()
        for split in queryset:
            self.assertNotEqual(split.transaction.interval,
                                RecurringTransaction.DISABLED)

    def test_personal(self):
        queryset = RecurringSplit.objects.personal()
        # we should get exactly 5 results. One for each, plus an additional for a transfer
        self.assertEqual(queryset.count(), 5)

    def test_transfers_once(self):
        queryset = RecurringSplit.objects.transfers_once()
        # this time we should get exactly 4.
        self.assertEqual(queryset.count(), 4)

    def test_exclude_transfers(self):
        queryset = RecurringSplit.objects.personal().exclude_transfers()
        # this time we get 3. the transfer is not included
        self.assertEqual(queryset.count(), 3)

    def test_income(self):
        queryset = RecurringSplit.objects.personal().income()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.deposit_transaction)

    def test_expense(self):
        queryset = RecurringSplit.objects.personal().expense()
        self.assertEqual(queryset.count(), 2)
        queryset = queryset.past()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.withdraw_transaction)

    def test_date_range_includes_start(self):
        queryset = RecurringSplit.objects.personal().date_range(date(2017, 6, 1), date(2017, 7, 1))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.deposit_transaction)

    def test_date_range_includes_end(self):
        queryset = RecurringSplit.objects.personal().date_range(date(2017, 5, 1), date(2017, 6, 1))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.deposit_transaction)

    def test_category(self):
        category = Category.objects.create(name='category')
        for s in self.withdraw_transaction.splits.all():
            s.category = category
            s.save()
        queryset = RecurringSplit.objects.personal().category(category)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.withdraw_transaction)

    def test_upcoming(self):
        queryset = RecurringSplit.objects.personal().upcoming()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.upcoming_transaction)

    def test_past(self):
        queryset = RecurringSplit.objects.personal().exclude_transfers().past()
        self.assertEqual(queryset.count(), 2)


class RecurringSplitModelTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='personal')
        self.savings = Account.objects.create(name='savings')
        self.foreign = Account.objects.create(name='foreign', account_type=Account.FOREIGN)

    def test_str_method(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.savings, 100, RecurringTransaction.TRANSFER,
            RecurringTransaction.MONTHLY)
        split = recurrence.splits.first()
        self.assertEqual(str(split), split.title)

    def test_split_absolute_url(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.savings, 100, RecurringTransaction.TRANSFER,
            RecurringTransaction.MONTHLY)
        split = recurrence.splits.first()
        self.assertEqual(split.get_absolute_url(),
                         reverse('recurrence_detail', args=[split.transaction.id]))

    def test_is_transfer(self):
        recurrence = create_recurring_transaction(
            'recurrence', self.personal, self.savings, 100, RecurringTransaction.TRANSFER,
            RecurringTransaction.MONTHLY)
        for split in recurrence.splits.all():
            self.assertTrue(split.is_transfer)
            self.assertFalse(split.is_withdraw)
            self.assertFalse(split.is_deposit)

    def test_is_withdraw(self):
        recurrence = create_recurring_transaction(
            'recurrence', self.personal, self.foreign, 100, RecurringTransaction.WITHDRAW,
            RecurringTransaction.MONTHLY)
        for split in recurrence.splits.all():
            self.assertTrue(split.is_withdraw)
            self.assertFalse(split.is_transfer)
            self.assertFalse(split.is_deposit)

    def test_is_deposit(self):
        recurrence = create_recurring_transaction(
            'recurrence', self.foreign, self.personal, 100, RecurringTransaction.DEPOSIT,
            RecurringTransaction.MONTHLY)
        for split in recurrence.splits.all():
            self.assertTrue(split.is_deposit)
            self.assertFalse(split.is_transfer)
            self.assertFalse(split.is_withdraw)

    def test_is_disabled(self):
        disabled_recurrence = create_recurring_transaction(
            'recurrence', self.foreign, self.personal, 100, RecurringTransaction.DEPOSIT,
            RecurringTransaction.DISABLED)
        recurrence = create_recurring_transaction(
            'recurrence', self.foreign, self.personal, 100, RecurringTransaction.DEPOSIT,
            RecurringTransaction.MONTHLY)
        disabled_split = disabled_recurrence.splits.first()
        split = recurrence.splits.first()
        self.assertTrue(disabled_split.is_disabled)
        self.assertFalse(split.is_disabled)
