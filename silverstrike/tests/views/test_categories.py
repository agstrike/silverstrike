from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from silverstrike.models import Account, Category, Transaction
from silverstrike.tests import create_transaction


class ViewTests(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin', email='email@example.com', password='pass')
        self.client.login(username='admin', password='pass')
        self.account = Account.objects.create(name='first account', show_on_dashboard=True)
        self.personal = Account.objects.create(name='personal account')
        self.expense = Account.objects.create(
            name="expense account", account_type=Account.AccountType.FOREIGN)
        self.revenue = Account.objects.create(
            name="revenue account", account_type=Account.AccountType.FOREIGN)

    def test_context_CategoryIndex_with_no_categories(self):
        context = self.client.get(reverse('category_by_month')).context
        self.assertEqual(context['menu'], 'categories')
        self.assertFalse('submenu' in context)
        self.assertEqual(context['categories'], [])

    def test_context_CategoryIndex_with_category(self):
        Category.objects.create(name='Some name')
        response = self.client.get(reverse('category_by_month'))
        self.assertEqual(response.status_code, 200)
        categories = response.context['categories']
        self.assertEqual(categories, [])

    def test_context_CategoryIndex_with_category_with_transactions(self):
        category = Category.objects.create(name='expenses')
        create_transaction('Deposit', self.revenue, self.account, 1500,
                           Transaction.DEPOSIT, category=category)
        create_transaction('Withdraw', self.account, self.expense, 500,
                           Transaction.WITHDRAW, category=category)
        response = self.client.get(reverse('category_by_month'))
        self.assertEqual(response.status_code, 200)
        categories = response.context['categories']
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0]['name'], category.name)
        self.assertEqual(categories[0]['spent'], -500)
        self.assertEqual(categories[0]['income'], 1500)
