from django.test import TestCase
from django.urls import reverse

from silverstrike.models import Account, AccountType, Category, Split, Transaction


class CategoryModelTests(TestCase):
    def test_category_str_method(self):
        category = Category.objects.create(name='category')
        self.assertEqual(str(category), category.name)

    def test_category_money_spent(self):
        category = Category.objects.create(name='category')
        self.assertEqual(category.money_spent, 0)

        account = Account.objects.create(name='some_account')
        expense = Account.objects.create(
            name='some_account', account_type=AccountType.FOREIGN)
        transaction = Transaction.objects.create(title='transaction',
                                                 transaction_type=Transaction.WITHDRAW,
                                                 src=account, dst=expense, amount=25.02)
        t = Split.objects.create(
            account=account, opposing_account=expense,
            transaction=transaction, amount=-25.02, category=category)
        Split.objects.create(
            account=expense, opposing_account=account,
            transaction=transaction, amount=25.02, category=category)

        self.assertEqual(float(category.money_spent), -t.amount)

    def test_category_absolute_url(self):
        category = Category.objects.create(name='foo')
        self.assertEqual(category.get_absolute_url(), reverse('category_detail',
                                                              args=[category.id]))
