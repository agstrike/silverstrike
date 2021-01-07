import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from silverstrike.models import Account


class ApiTests(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin', email='email@example.com', password='pass')
        self.client.login(username='admin', password='pass')
        Account.objects.bulk_create(
            [Account(name=t[1], account_type=t[0],
                     show_on_dashboard=True) for t in Account.AccountType.choices])

    def test_get_accounts_return_value(self):
        for t in Account.AccountType.choices:
            response = self.client.get(reverse('api_accounts', args=[t[1].upper()]))
            data = json.loads(response.content.decode('utf-8'))
            queryset = Account.objects.filter(account_type=t[0])
            queryset = queryset.exclude(account_type=Account.AccountType.SYSTEM)
            self.assertEqual(data, list(queryset.values_list('name', flat=True)))

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
