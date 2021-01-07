from django.contrib.auth.models import User
from django.test import TestCase

from silverstrike.models import Account, Split


class AccountQuerysetTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='Personal')
        self.foreign = Account.objects.create(
            name='foreign',
            account_type=Account.AccountType.FOREIGN)

    def test_personal_queryset(self):
        queryset = Account.objects.personal()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), self.personal)

    def test_foreign_queryset(self):
        queryset = Account.objects.foreign()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first(), self.foreign)

    def test_active_queryset(self):
        queryset = Account.objects.active()
        # since foreign and system account are also active they are returned here
        self.assertEqual(queryset.count(), 3)
        self.personal.active = False
        self.personal.save()
        # now it should only be two
        queryset = Account.objects.active()
        self.assertEqual(queryset.count(), 2)

    def test_inactive_queryset(self):
        queryset = Account.objects.inactive()
        self.assertEqual(queryset.count(), 0)
        self.personal.active = False
        self.personal.save()

        queryset = Account.objects.inactive()
        self.assertEqual(queryset.count(), 1)


class AccountModelTests(TestCase):
    def test_account_str_method(self):
        account = Account.objects.create(name='some_account')
        self.assertEqual(str(account), account.name)
        User.objects.create_superuser(username='admin', email='admin@example.com', password='pass')
        self.client.login(username='admin', password='pass')
        response = self.client.get(account.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['account'], account)

    def test_account_type_str_method(self):
        account = Account.objects.create(name='first')
        self.assertEqual(account.account_type_str, 'Personal')
        account.account_type = Account.AccountType.FOREIGN
        self.assertEqual(account.account_type_str, 'Foreign')
        account.account_type = Account.AccountType.SYSTEM
        self.assertEqual(account.account_type_str, 'System')

    def test_account_transaction_number(self):
        account = Account.objects.create(name='foo')
        self.assertEqual(account.transaction_num, 0)
        account.set_initial_balance(50)
        self.assertEqual(account.transaction_num, 1)

    def test_set_initial_balance(self):
        account = Account.objects.create(name='foo')
        self.assertEqual(account.balance, 0)
        account.set_initial_balance(50)
        self.assertEqual(account.balance, 50)
        # repeated calls to set initial balance keep adding to it
        account.set_initial_balance(50)
        self.assertEqual(account.balance, 100)

    def test_account_balance_with_no_transactions(self):
        account = Account.objects.create(name='some_account')
        self.assertEqual(account.balance, 0)

    def test_initial_balance_is_system(self):
        account = Account.objects.create(name='foo')
        account.set_initial_balance(10)
        split = Split.objects.first()
        self.assertTrue(split.is_system)
