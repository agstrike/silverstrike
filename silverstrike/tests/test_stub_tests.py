from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from silverstrike.models import Account, AccountType


class AccountIndexViewTests(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin', email='email@example.com', password='pass')
        self.client.login(username='admin', password='pass')
        self.account = Account.objects.create(name='first account', show_on_dashboard=True)
        self.personal = Account.objects.create(name='personal account')
        self.expense = Account.objects.create(
            name="expense account", account_type=AccountType.FOREIGN)
        self.revenue = Account.objects.create(
            name="revenue account", account_type=AccountType.FOREIGN)

    def test_ChartView(self):
        # TODO
        self.client.get(reverse('charts'))

    def test_api_accounts_balance(self):
        # TODO
        self.client.get(reverse('api_accounts_balance', args=['2017-01-01', '2017-06-01']))
