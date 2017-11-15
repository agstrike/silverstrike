from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from silverstrike.models import Account


class IndexViewTestCase(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin', email='email@example.com', password='pass')
        self.client.login(username='admin', password='pass')
        self.account = Account.objects.create(name='first account', show_on_dashboard=True)
        self.personal = Account.objects.create(name='personal account')
        self.expense = Account.objects.create(
            name="expense account", account_type=Account.FOREIGN)
        self.revenue = Account.objects.create(
            name="revenue account", account_type=Account.FOREIGN)

    def test_menu_entry_IndexView(self):
        context = self.client.get(reverse('index')).context
        self.assertEquals(context['menu'], 'home')

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
