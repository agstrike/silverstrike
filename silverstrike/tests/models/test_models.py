from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from silverstrike.models import Account, Category, Split, Transaction


class ModelTests(TestCase):
    def test_account_str_method(self):
        account = Account.objects.create(name="some_account")
        self.assertEqual(str(account), account.name)
        User.objects.create_superuser(username='admin', email='admin@example.com', password='pass')
        self.client.login(username='admin', password='pass')
        response = self.client.get(account.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['account'], account)

    def test_account_type_str_method(self):
        account = Account.objects.create(name='first')
        self.assertEqual(account.account_type_str, 'Personal')
        account.account_type = Account.FOREIGN
        self.assertEqual(account.account_type_str, 'Foreign')
        account.account_type = Account.SYSTEM
        self.assertEqual(account.account_type_str, 'System')

    def test_account_transaction_number(self):
        account = Account.objects.create(name="foo")
        self.assertEqual(account.transaction_num, 0)
        account.set_initial_balance(50)
        self.assertEqual(account.transaction_num, 1)

    def test_set_initial_balance(self):
        account = Account.objects.create(name="foo")
        self.assertEqual(account.balance, 0)
        account.set_initial_balance(50)
        self.assertEqual(account.balance, 50)
        # repeated calls to set initial balance keep adding to it
        account.set_initial_balance(50)
        self.assertEqual(account.balance, 100)

    def test_account_balance_with_no_transactions(self):
        account = Account.objects.create(name="some_account")
        self.assertEqual(account.balance, 0)

    def test_transaction_str_method(self):
        account = Account.objects.create(name="some_account")
        expense = Account.objects.create(
            name="some_account", account_type=Account.FOREIGN)
        transaction = Transaction.objects.create(title="transaction",
                                                 transaction_type=Transaction.WITHDRAW)
        self.assertEqual(str(transaction), transaction.title)
        transaction = Split.objects.create(
            account=account, opposing_account=expense,
            transaction=transaction, amount=-25.02, title='meh')
        self.assertEqual(str(transaction), transaction.title)

    def test_category_str_method(self):
        category = Category.objects.create(name="cat 1")
        self.assertEqual(str(category), category.name)

    def test_category_money_spent(self):
        category = Category.objects.create(name="cat 1")
        self.assertEqual(category.money_spent, 0)

        account = Account.objects.create(name="some_account")
        expense = Account.objects.create(
            name="some_account", account_type=Account.FOREIGN)
        transaction = Transaction.objects.create(title="transaction",
                                                 transaction_type=Transaction.WITHDRAW)
        t = Split.objects.create(
            account=account, opposing_account=expense,
            transaction=transaction, amount=-25.02, category=category)
        Split.objects.create(
            account=expense, opposing_account=account,
            transaction=transaction, amount=25.02, category=category)

        self.assertEqual(float(category.money_spent), -t.amount)

    def test_transaction_amount(self):
        account = Account.objects.create(name="foo")
        account.set_initial_balance(10)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.amount, 10)

    def test_split_is_system(self):
        account = Account.objects.create(name="foo")
        account.set_initial_balance(10)
        split = Split.objects.first()
        self.assertTrue(split.is_system)

    def test_split_absolute_url(self):
        account = Account.objects.create(name="foo")
        account.set_initial_balance(10)
        split = Split.objects.first()
        self.assertEqual(split.get_absolute_url(), reverse('transaction_detail',
                                                           args=[split.transaction.id]))

    def test_category_absolute_url(self):
        category = Category.objects.create(name="foo")
        self.assertEqual(category.get_absolute_url(), reverse('category_detail',
                                                              args=[category.id]))
