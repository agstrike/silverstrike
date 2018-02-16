from datetime import date

from dateutil.relativedelta import relativedelta

from django.test import TestCase
from django.urls import reverse

from silverstrike.models import Account, RecurringTransaction, Transaction


class RecurrenceTests(TestCase):
    def setUp(self):
        personal = Account.objects.create(name='personal')
        foreign = Account.objects.create(name='foreign', account_type=Account.FOREIGN)

        self.date = date(2018, 1, 1)
        self.recurrence = RecurringTransaction.objects.create(
            title='some recurrence',
            amount=25,
            date=self.date,
            src=personal,
            dst=foreign,
            recurrence=RecurringTransaction.MONTHLY,
            transaction_type=Transaction.WITHDRAW)

    def test_str_method(self):
        self.assertEquals('{}'.format(self.recurrence), 'some recurrence')

    def test_absolute_url(self):
        self.assertEquals(self.recurrence.get_absolute_url(),
                          reverse('recurrence_detail', args=[self.recurrence.pk]))

    def test_past_date_is_due(self):
        self.assertTrue(self.recurrence.is_due)

    def test_current_date_is_due(self):
        self.recurrence.date = date.today()
        self.assertTrue(self.recurrence.is_due)

    def test_future_date_is_not_due(self):
        self.recurrence.date = date(2100, 1, 1)
        self.assertFalse(self.recurrence.is_due)

    def test_update_monthly(self):
        self.recurrence.update_date()
        self.assertEquals(self.recurrence.date, self.date + relativedelta(months=1))

    def test_update_quarterly(self):
        self.recurrence.recurrence = RecurringTransaction.QUARTERLY
        self.recurrence.update_date()
        self.assertEquals(self.recurrence.date, self.date + relativedelta(months=3))

    def test_update_biannually(self):
        self.recurrence.recurrence = RecurringTransaction.BIANNUALLY
        self.recurrence.update_date()
        self.assertEquals(self.recurrence.date, self.date + relativedelta(months=6))

    def test_update_annually(self):
        self.recurrence.recurrence = RecurringTransaction.ANNUALLY
        self.recurrence.update_date()
        self.assertEquals(self.recurrence.date, self.date + relativedelta(months=12))

    def test_update_disabled_recurrences(self):
        self.recurrence.recurrence = RecurringTransaction.DISABLED
        self.recurrence.update_date()
        self.assertEquals(self.recurrence.date, self.date)

    def test_active_recurrences_are_not_disabled(self):
        self.assertFalse(self.recurrence.is_disabled)

    def test_disabled_recurrences_are_disabled(self):
        self.recurrence.recurrence = RecurringTransaction.DISABLED
        self.assertTrue(self.recurrence.is_disabled)

    def test_recurrence_string(self):
        self.assertEquals(self.recurrence.get_recurrence, 'Monthly')

    def test_signed_amount_for_withdraws(self):
        self.assertEquals(self.recurrence.signed_amount, -25)

    def test_signed_amount_for_deposits(self):
        self.recurrence.transaction_type = Transaction.DEPOSIT
        self.assertEquals(self.recurrence.signed_amount, 25)

    def test_is_withdraw_method(self):
        self.assertTrue(self.recurrence.is_withdraw)
        self.assertFalse(self.recurrence.is_deposit)

    def test_is_deposit_method(self):
        self.recurrence.transaction_type = Transaction.DEPOSIT
        self.assertTrue(self.recurrence.is_deposit)
        self.assertFalse(self.recurrence.is_withdraw)

    def test_average_amount(self):
        # TODO add a test
        pass

    def test_outstanding_sum(self):
        # TODO add a test
        pass

    def test_due_in_month_queryset(self):
        # TODO add a test
        pass
