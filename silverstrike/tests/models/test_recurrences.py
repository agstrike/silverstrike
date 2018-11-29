from datetime import date

from dateutil.relativedelta import relativedelta

from django.test import TestCase
from django.urls import reverse

from silverstrike.models import Account, RecurringTransaction, Transaction
from silverstrike.tests import create_recurring_transaction, create_transaction


class RecurringTransactionQuerySetTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='personal')
        self.savings = Account.objects.create(name='savings')
        self.foreign = Account.objects.create(name='foreign', account_type=Account.FOREIGN)
        self.date = date(2018, 1, 31)

    def test_due_in_month(self):
        last_day_of_month = date(date.today().year, date.today().month + 1, 1)
        last_day_of_month = last_day_of_month - relativedelta(days=1)
        for diff in [1, 2, 5]:
            create_recurring_transaction(
                'recurrence',
                self.personal,
                self.foreign,
                100,
                RecurringTransaction.WITHDRAW,
                RecurringTransaction.MONTHLY,
                date=date.today() +
                relativedelta(
                    years=diff,
                    months=diff,
                    days=diff))
            create_recurring_transaction(
                'recurrence',
                self.personal,
                self.foreign,
                100,
                RecurringTransaction.WITHDRAW,
                RecurringTransaction.MONTHLY,
                date=date.today() -
                relativedelta(
                    years=diff,
                    months=diff,
                    days=diff))
        queryset = RecurringTransaction.objects.due_in_month()
        for recurrence in queryset:
            self.assertLessEqual(recurrence.date, last_day_of_month)

    def test_not_disabled(self):
        create_recurring_transaction(
            'disabled',
            self.personal,
            self.foreign,
            100,
            RecurringTransaction.WITHDRAW,
            RecurringTransaction.DISABLED)
        create_recurring_transaction('daily', self.personal, self.foreign, 100,
                                     RecurringTransaction.WITHDRAW, RecurringTransaction.DAILY)
        create_recurring_transaction('weekly', self.personal, self.foreign, 100,
                                     RecurringTransaction.WITHDRAW, RecurringTransaction.WEEKLY)
        create_recurring_transaction(
            'monthly',
            self.personal,
            self.foreign,
            100,
            RecurringTransaction.WITHDRAW,
            RecurringTransaction.MONTHLY)
        create_recurring_transaction(
            'annually',
            self.personal,
            self.foreign,
            100,
            RecurringTransaction.WITHDRAW,
            RecurringTransaction.ANNUALLY)
        queryset = RecurringTransaction.objects.not_disabled()
        for recurrence in queryset:
            self.assertNotEqual(recurrence.recurrence, RecurringTransaction.DISABLED)


class RecurrenceTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='personal')
        self.savings = Account.objects.create(name='savings')
        self.foreign = Account.objects.create(name='foreign',
                                              account_type=Account.FOREIGN)

    def test_str_method(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.MONTHLY)
        self.assertEquals(str(recurrence), 'some recurrence')

    def test_absolute_url(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.MONTHLY)
        self.assertEquals(recurrence.get_absolute_url(),
                          reverse('recurrence_detail', args=[recurrence.pk]))

    def test_past_date_is_due(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.MONTHLY,
            date=date.today() - relativedelta(months=3))
        self.assertTrue(recurrence.is_due)

    def test_current_date_is_due(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.MONTHLY)
        self.assertTrue(recurrence.is_due)

    def test_future_date_is_not_due(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.MONTHLY,
            date=date.today() + relativedelta(months=3))
        self.assertFalse(recurrence.is_due)

    def test_update_daily(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.DAILY)
        recurrence.update_date(save=True)
        self.assertEquals(recurrence.date, date.today() + relativedelta(days=1))
        for split in recurrence.splits.all():
            self.assertEquals(split.date, date.today() + relativedelta(days=1))

    def test_update_weekly(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.WEEKLY)
        recurrence.update_date(save=True)
        self.assertEquals(
            recurrence.date, date.today() + relativedelta(weeks=1))
        for split in recurrence.splits.all():
            self.assertEquals(split.date, date.today() + relativedelta(weeks=1))

    def test_update_monthly(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.MONTHLY)
        recurrence.update_date(save=True)
        self.assertEquals(recurrence.date, date.today() + relativedelta(months=1))
        for split in recurrence.splits.all():
            self.assertEquals(
                split.date, date.today() + relativedelta(months=1))

    def test_update_quarterly(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.QUARTERLY)
        recurrence.update_date(save=True)
        self.assertEquals(
            recurrence.date, date.today() + relativedelta(months=3))
        for split in recurrence.splits.all():
            self.assertEquals(
                split.date, date.today() + relativedelta(months=3))

    def test_update_biannually(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.BIANNUALLY)
        recurrence.update_date(save=True)
        self.assertEquals(
            recurrence.date, date.today() + relativedelta(months=6))
        for split in recurrence.splits.all():
            self.assertEquals(
                split.date, date.today() + relativedelta(months=6))

    def test_update_annually(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.ANNUALLY)
        recurrence.update_date(save=True)
        self.assertEquals(recurrence.date, date.today() + relativedelta(years=1))
        for split in recurrence.splits.all():
            self.assertEquals(split.date, date.today() + relativedelta(years=1))

    def test_update_skip(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.WEEKLY)
        for skip in range(1, 2):
            recurrence.skip = skip
            recurrence.update_date(save=True)
            self.assertEquals(recurrence.date,
                              date.today() + relativedelta(weeks=skip + 1))

    def test_weekend_handling_skip(self):
        pass
        """
        Not implemented yet
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.DAILY,
            date=date(2018, 1, 1))
        recurrence.skip = 4
        recurrence.weekend_handling = RecurringTransaction.SKIP
        recurrence.update_date(save=True)
        self.assertEquals(recurrence.date, date(2018, 1, 11))
        """

    def test_weekend_handling_previous(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.DAILY,
            date=date(2018, 1, 1))
        recurrence.skip = 4
        recurrence.weekend_handling = RecurringTransaction.PREVIOUS_WEEKDAY
        recurrence.update_date(save=True)
        self.assertEquals(recurrence.date, date(2018, 1, 1) + relativedelta(days=4))

    def test_weekend_handling_next(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.DAILY,
            date=date(2018, 1, 1))
        recurrence.skip = 4
        recurrence.weekend_handling = RecurringTransaction.NEXT_WEEKDAY
        recurrence.update_date(save=True)
        self.assertEquals(recurrence.date, date(2018, 1, 1) + relativedelta(weeks=1))

    def test_last_day_of_month(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.DAILY,
            date=date(2018, 1, 1), last_day_in_month=True)
        recurrence.update_date(save=True)
        self.assertEquals(recurrence.date, date(2018, 1, 31))

    def test_update_disabled_recurrences(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.DISABLED)
        recurrence.update_date(save=True)
        self.assertEquals(recurrence.date, date.today())

    def test_active_recurrences_are_not_disabled(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.WEEKLY)
        self.assertFalse(recurrence.is_disabled)

    def test_disabled_recurrences_are_disabled(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.DISABLED)
        self.assertTrue(recurrence.is_disabled)

    def test_recurrence_string(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.MONTHLY)
        self.assertEquals(recurrence.get_recurrence, 'Monthly')

    def test_amount_for_withdraws(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.WEEKLY)
        self.assertEquals(recurrence.amount, -100)

    def test_amount_for_deposits(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.foreign, self.personal, 100,
            RecurringTransaction.DEPOSIT, RecurringTransaction.WEEKLY)
        self.assertEquals(recurrence.amount, 100)

    def test_amount_for_transfers(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.savings, 100,
            RecurringTransaction.TRANSFER, RecurringTransaction.WEEKLY)
        self.assertEquals(recurrence.amount, 100)

    def test_is_withdraw_method(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.WEEKLY)
        self.assertTrue(recurrence.is_withdraw)
        self.assertFalse(recurrence.is_deposit)
        self.assertFalse(recurrence.is_transfer)

    def test_is_deposit_method(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.foreign, self.personal, 100,
            RecurringTransaction.DEPOSIT, RecurringTransaction.WEEKLY)
        self.assertTrue(recurrence.is_deposit)
        self.assertFalse(recurrence.is_withdraw)
        self.assertFalse(recurrence.is_transfer)

    def test_is_transfer_method(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.savings, 100,
            RecurringTransaction.TRANSFER, RecurringTransaction.WEEKLY)
        self.assertTrue(recurrence.is_transfer)
        self.assertFalse(recurrence.is_deposit)
        self.assertFalse(recurrence.is_withdraw)

    def test_average_amount_for_withdrawls(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.WEEKLY)
        for i in range(1, 11):
            t = create_transaction('meh', self.personal, self.foreign, i * 10, Transaction.WITHDRAW)
            t.recurrence = recurrence
            t.save()
        self.assertEquals(recurrence.average_amount, -sum([i * 10 for i in range(1, 11)]) / 10)

    def test_average_amount_for_deposits(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.foreign, self.personal, 100,
            RecurringTransaction.DEPOSIT, RecurringTransaction.WEEKLY)
        for i in range(1, 11):
            t = create_transaction('meh', self.foreign, self.personal, i * 10, Transaction.DEPOSIT)
            t.recurrence = recurrence
            t.save()
        self.assertEquals(recurrence.average_amount, sum([i * 10 for i in range(1, 11)]) / 10)

    def test_average_amount_for_transfers(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.savings, 100,
            RecurringTransaction.TRANSFER, RecurringTransaction.WEEKLY)
        for i in range(1, 11):
            t = create_transaction('meh', self.personal, self.savings, i * 10, Transaction.TRANSFER)
            t.recurrence = recurrence
            t.save()
        self.assertEquals(recurrence.average_amount, 0)

    def test_outstanding_sum(self):
        # TODO add a test
        pass

    def test_sum_amount_for_withdrawls(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.WEEKLY)
        for year in [1999, 2000, 2001]:
            for month in [1, 6, 12]:
                for day in [1, 15, 28]:
                    transaction = create_transaction(
                        recurrence.title, self.personal, self.foreign, 100,
                        recurrence.transaction_type, date=date(year, month, day))
                    transaction.recurrence = recurrence
                    transaction.save()
        self.assertEqual(recurrence.sum_amount(), -2700)
        self.assertEqual(recurrence.sum_amount(date(2000, 1, 1), date(2000, 12, 28)), -900)
        self.assertEqual(recurrence.sum_amount(date(2001, 1, 1), date(2001, 1, 31)), -300)
        self.assertEqual(recurrence.sum_amount(date(1999, 1, 1), date(1999, 1, 2)), -100)
        self.assertEqual(recurrence.sum_amount(date(1999, 1, 1), date(2001, 12, 28)), -2700)

    def test_sum_amount_for_deposits(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.foreign, self.personal, 100,
            RecurringTransaction.DEPOSIT, RecurringTransaction.WEEKLY)
        for year in [1999, 2000, 2001]:
            for month in [1, 6, 12]:
                for day in [1, 15, 28]:
                    transaction = create_transaction(
                        recurrence.title, self.foreign, self.personal, 100,
                        recurrence.transaction_type, date=date(year, month, day))
                    transaction.recurrence = recurrence
                    transaction.save()
        self.assertEqual(recurrence.sum_amount(), 2700)
        self.assertEqual(recurrence.sum_amount(date(2000, 1, 1), date(2000, 12, 28)), 900)
        self.assertEqual(recurrence.sum_amount(date(2001, 1, 1), date(2001, 1, 31)), 300)
        self.assertEqual(recurrence.sum_amount(date(1999, 1, 1), date(1999, 1, 2)), 100)
        self.assertEqual(recurrence.sum_amount(date(1999, 1, 1), date(2001, 12, 28)), 2700)

    def test_sum_amount_for_transfers(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.savings, 100,
            RecurringTransaction.TRANSFER, RecurringTransaction.WEEKLY)
        for year in [1999, 2000, 2001]:
            for month in [1, 6, 12]:
                for day in [1, 15, 28]:
                    transaction = create_transaction(
                        recurrence.title, self.personal, self.savings, 100,
                        recurrence.transaction_type, date=date(year, month, day))
                    transaction.recurrence = recurrence
                    transaction.save()
        self.assertEqual(recurrence.sum_amount(), 0)
        self.assertEqual(recurrence.sum_amount(date(2000, 1, 1), date(2000, 12, 28)), 0)
        self.assertEqual(recurrence.sum_amount(date(2001, 1, 1), date(2001, 1, 31)), 0)
        self.assertEqual(recurrence.sum_amount(date(1999, 1, 1), date(1999, 1, 2)), 0)
        self.assertEqual(recurrence.sum_amount(date(1999, 1, 1), date(2001, 12, 28)), 0)

    def test_sum_future_amount_for_withdrawals(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.foreign, 100,
            RecurringTransaction.WITHDRAW, RecurringTransaction.WEEKLY, date=date(2000, 1, 1))
        self.assertEqual(recurrence.sum_future_amount(date(2000, 1, 31)), -500)
        self.assertEqual(recurrence.sum_future_amount(date(2000, 1, 7)), -100)
        self.assertEqual(recurrence.sum_future_amount(date(1999, 1, 1)), 0)

    def test_sum_future_amount_for_deposits(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.foreign, self.personal, 100,
            RecurringTransaction.DEPOSIT, RecurringTransaction.WEEKLY, date=date(2000, 1, 1))
        self.assertEqual(recurrence.sum_future_amount(date(2000, 1, 31)), 500)
        self.assertEqual(recurrence.sum_future_amount(date(2000, 1, 7)), 100)
        self.assertEqual(recurrence.sum_future_amount(date(1999, 1, 1)), 0)

    def test_sum_future_amount_for_transfers(self):
        recurrence = create_recurring_transaction(
            'some recurrence', self.personal, self.savings, 100,
            RecurringTransaction.TRANSFER, RecurringTransaction.WEEKLY, date=date(2000, 1, 1))
        self.assertEqual(recurrence.sum_future_amount(date(2000, 1, 31)), 500)
        self.assertEqual(recurrence.sum_future_amount(date(2000, 1, 7)), 100)
        self.assertEqual(recurrence.sum_future_amount(date(1999, 1, 1)), 0)
