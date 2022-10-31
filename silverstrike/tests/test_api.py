import json
from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from silverstrike.models import Account, AccountType, Transaction
from silverstrike.tests import create_transaction


class ApiTests(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin', email='email@example.com', password='pass')
        self.client.login(username='admin', password='pass')
        self.personal = Account.objects.create(name="Personal", account_type=AccountType.PERSONAL,
                                               show_on_dashboard=True)
        self.foreign = Account.objects.create(name="Foreign", account_type=AccountType.FOREIGN,
                                              show_on_dashboard=True)
        self.system = Account.objects.create(name="System", account_type=AccountType.SYSTEM,
                                             show_on_dashboard=True)
        self.cash = Account.objects.create(name="Cash", account_type=AccountType.PERSONAL,
                                           show_on_dashboard=False)
        create_transaction('meh', self.foreign, self.personal, 1000,
                           Transaction.DEPOSIT, date(2022, 1, 2))
        create_transaction('meh', self.foreign, self.cash, 1000,
                           Transaction.DEPOSIT, date(2022, 1, 3))

    def test_get_accounts_return_value(self):
        for t in AccountType.choices:
            response = self.client.get(reverse('api_accounts', args=[t[1].upper()]))
            data = json.loads(response.content.decode('utf-8'))
            queryset = Account.objects.filter(account_type=t[0])
            queryset = queryset.exclude(account_type=AccountType.SYSTEM)
            self.assertEqual(data, list(queryset.values_list('name', flat=True)))

    def test_get_balance_data_excludes_non_dashboard_accounts(self):
        response = self.client.get(reverse('api_balance', args=['2022-01-02', '2022-01-02']))
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(['1000.00'], data.get('data'))

    def test_get_non_dashboard_balance_return_value(self):
        response = self.client.get(reverse('api_non_dashboard_balance', args=['2022-01-03', '2022-01-03']))
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(['2000.00'], data.get('data'))

    def test_get_account_balance_invalid_date(self):
        response = self.client.get(reverse('api_account_balance', args=['1', '2019-01-01', '20']))
        self.assertEqual(response.status_code, 400)
        response = self.client.get(
            reverse('api_account_balance', args=['1', '2019-13-01', '2019-01-01']))
        self.assertEqual(response.status_code, 400)

    def test_get_account_balance_unknown_account(self):
        response = self.client.get(
            reverse('api_account_balance', args=['0', '2019-01-01', '2019-02-01']))
        self.assertEqual(response.status_code, 404)

    def test_get_balances_invalid_date(self):
        response = self.client.get(reverse('api_accounts_balance', args=['2019-01-01', '20']))
        self.assertEqual(response.status_code, 400)
        response = self.client.get(
            reverse('api_accounts_balance', args=['2019-13-01', '2019-01-01']))
        self.assertEqual(response.status_code, 400)

    def test_category_spending_invalid_date(self):
        response = self.client.get(reverse('category_spending', args=['2019-01-01', '20']))
        self.assertEqual(response.status_code, 400)
        response = self.client.get(reverse('category_spending', args=['2019-13-01', '2019-01-01']))
        self.assertEqual(response.status_code, 400)
