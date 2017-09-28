from django.contrib.auth.models import User
from django.test import TestCase

from silverstrike.models import Account, Category, Split, Transaction


class ModelTests(TestCase):
    def test_account_str_method(self):
        account = Account.objects.create(name="some_account")
        self.assertEquals(str(account), account.name)
        User.objects.create_superuser(username='admin', email='admin@example.com', password='pass')
        self.client.login(username='admin', password='pass')
        response = self.client.get(account.get_absolute_url())
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['account'], account)

    def test_account_balance_with_no_transactions(self):
        account = Account.objects.create(name="some_account")
        self.assertEquals(account.balance, 0)

    def test_transaction_str_method(self):
        account = Account.objects.create(name="some_account")
        expense = Account.objects.create(
            name="some_account", account_type=Account.EXPENSE)
        journal = Transaction.objects.create(title="journal",
                                             transaction_type=Transaction.WITHDRAW)
        self.assertEquals(str(journal), journal.title)
        transaction = Split.objects.create(
            account=account, opposing_account=expense,
            journal=journal, amount=-25.02, title='meh')
        self.assertEquals(str(transaction), transaction.title)

    def test_category_str_method(self):
        category = Category.objects.create(name="cat 1")
        self.assertEquals(str(category), category.name)

    def test_category_money_spent(self):
        category = Category.objects.create(name="cat 1")
        self.assertEquals(category.money_spent, 0)

        account = Account.objects.create(name="some_account")
        expense = Account.objects.create(
            name="some_account", account_type=Account.EXPENSE)
        journal = Transaction.objects.create(title="journal",
                                             transaction_type=Transaction.WITHDRAW)
        t = Split.objects.create(
            account=account, opposing_account=expense,
            journal=journal, amount=-25.02, category=category)
        Split.objects.create(
            account=expense, opposing_account=account,
            journal=journal, amount=25.02, category=category)

        self.assertEquals(float(category.money_spent), -t.amount)
