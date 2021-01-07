from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from silverstrike.models import Account, Transaction
from silverstrike.tests import create_transaction


class IndexViewTestCase(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin', email='email@example.com', password='pass')
        self.client.login(username='admin', password='pass')
        self.account = Account.objects.create(name='first account', show_on_dashboard=True)
        self.personal = Account.objects.create(name='personal')
        self.foreign = Account.objects.create(
            name="foreign account", account_type=Account.AccountType.FOREIGN)

    def test_menu_entry_IndexView(self):
        context = self.client.get(reverse('index')).context
        self.assertEqual(context['menu'], 'home')

    def test_empty_balance(self):
        context = self.client.get(reverse('index')).context
        self.assertEqual(context['balance'], 0)

    def test_balance_with_past_transactions(self):
        create_transaction('meh', self.foreign, self.account, 1000,
                           Transaction.DEPOSIT, date(2010, 1, 1))
        create_transaction('meh', self.foreign, self.personal, 1000,
                           Transaction.DEPOSIT, date(2015, 1, 1))
        create_transaction('meh', self.account, self.foreign, 500,
                           Transaction.WITHDRAW, date(2017, 1, 1))
        create_transaction('meh', self.personal, self.foreign, 500, Transaction.WITHDRAW)
        context = self.client.get(reverse('index')).context
        self.assertEqual(context['balance'], 1000)

    def test_balance_does_not_count_future_transactions(self):
        create_transaction('meh', self.foreign, self.account, 1000,
                           Transaction.DEPOSIT, date(2100, 1, 1))
        create_transaction('meh', self.personal, self.foreign, 500,
                           Transaction.WITHDRAW, date(2100, 1, 1))
        context = self.client.get(reverse('index')).context
        self.assertEqual(context['balance'], 0)

    def test_income(self):
        pass

    def test_expenses(self):
        pass

    def test_previous_income(self):
        pass

    def test_previous_expenses(self):
        pass

    def test_upcoming_transactions(self):
        pass

    def test_upcoming_recurrences(self):
        pass

    def test_outstanding_balance(self):
        pass
