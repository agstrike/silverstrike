from django.contrib.auth.models import User
from django.test import TestCase

from silverstrike.models import Account


class IndexViewTestCase(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin', email='email@example.com', password='pass')
        self.client.login(username='admin', password='pass')
        self.account = Account.objects.create(name='first account', show_on_dashboard=True)
        self.personal = Account.objects.create(name='personal account')
        self.expense = Account.objects.create(
            name="expense account", account_type=Account.EXPENSE)
        self.revenue = Account.objects.create(
            name="revenue account", account_type=Account.REVENUE)
