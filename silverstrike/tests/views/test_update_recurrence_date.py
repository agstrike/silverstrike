from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from silverstrike.models import Account, AccountType, RecurringTransaction, Transaction
from silverstrike.tests import create_transaction


class UpdateRecurrenceDateTests(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin', email='email@example.com', password='pass')
        self.client.login(username='admin', password='pass')
        self.account = Account.objects.create(name='first account')
        self.foreign = Account.objects.create(
            name="other account", account_type=AccountType.FOREIGN)
        self.recurrence = RecurringTransaction.objects.create(
            title='A recurrence',
            amount=500,
            date=date(2019, 1, 1),
            src=self.account,
            dst=self.foreign,
            interval=RecurringTransaction.MONTHLY,
            transaction_type=Transaction.WITHDRAW,
            usual_month_day=1
        )
        self.transaction = create_transaction('title', self.account, self.foreign, 500,
                                              Transaction.WITHDRAW, date(2019, 1, 1))
        self.transaction.recurrence = self.recurrence
        self.transaction.save()

    def test_no_update_when_transactions_are_in_past(self):
        self.recurrence.date = date(2019, 2, 1)
        response = self.client.post(reverse('update_current_recurrences'))
        self.assertRedirects(response, reverse('recurrences'))
        self.recurrence.refresh_from_db()
        self.assertEqual(self.recurrence.date, date(2019, 2, 1))

    def test_recurrence_gets_updated(self):
        response = self.client.post(reverse('update_current_recurrences'))
        self.assertRedirects(response, reverse('recurrences'))
        self.recurrence.refresh_from_db()
        self.assertEqual(self.recurrence.date, date(2019, 2, 1))

    def test_recurrence_with_no_transactions(self):
        self.transaction.delete()
        response = self.client.post(reverse('update_current_recurrences'))
        self.assertRedirects(response, reverse('recurrences'))
        self.recurrence.refresh_from_db()
        self.assertEqual(self.recurrence.date, date(2019, 1, 1))
