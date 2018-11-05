from django.test import TestCase

from silverstrike.models import Account, RecurringSplit, RecurringTransaction
from silverstrike.tests import create_recurring_transaction

class RecurringSplitQuerySetTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='personal')
        self.foreign = Account.objects.create(name='foreign', account_type=Account.FOREIGN)

    def test_not_disabled(self):
        create_recurring_transaction('disabled', self.personal, self.foreign,
            100, RecurringTransaction.WITHDRAW, RecurringTransaction.DISABLED)
        create_recurring_transaction('daily', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.DAILY)
        create_recurring_transaction('weekly', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.WEEKLY)
        create_recurring_transaction('monthly', self.personal, self.foreign,
            100, RecurringTransaction.WITHDRAW, RecurringTransaction.MONTHLY)
        create_recurring_transaction('annual', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.ANNUAL)
        for split in RecurringSplit.objects.not_disabled():
            self.assertEqual(split.recurrence.recurrence,
                RecurringTransaction.DISABLED)


class RecurringSplitModelTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='personal')
        self.savings = Account.objects.create(name='savings')
        self.foreign = Account.objects.create(name='foreign', account_type=Account.FOREIGN)

    def test_is_transfer(self):
        recurrence = create_recurring_transaction('recurrence', 
            self.personal, self.savings, 100, RecurringTransaction.TRANSFER, 
            RecurringTransaction.MONTHLY)
        for split in recurrence.splits.all():
            self.assertTrue(split.is_transfer)
            self.assertFalse(split.is_withdraw)
            self.assertFalse(split.is_deposit)
            self.assertFalse(split.is_system)

    def test_is_withdraw(self):
        recurrence = create_recurring_transaction('recurrence', 
            self.personal, self.foreign, 100, RecurringTransaction.WITHDRAW, 
            RecurringTransaction.MONTHLY)
        for split in recurrence.splits.all():
            self.assertTrue(split.is_withdraw)
            self.assertFalse(split.is_transfer)
            self.assertFalse(split.is_deposit)
            self.assertFalse(split.is_system)

    def test_is_deposit(self):
        recurrence = create_recurring_transaction('recurrence', 
            self.foreign, self.personal, 100, RecurringTransaction.DEPOSIT, 
            RecurringTransaction.MONTHLY)
        for split in recurrence.splits.all():
            self.assertTrue(split.is_deposit)
            self.assertFalse(split.is_withdraw)
            self.assertFalse(split.is_transfer)
            self.assertFalse(split.is_system)
