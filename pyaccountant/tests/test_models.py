from django.test import TestCase

from pyaccountant.models import Account, AccountType, InternalAccountType


class ModelTests(TestCase):
    def test_account_str_method(self):
        account = Account.objects.create(
            name="some_account", internal_type=InternalAccountType.personal.value)
        self.assertEquals(str(account), account.name)

    def test_accountType_str_method(self):
        accountType = AccountType.objects.create(name="some_account_type")
        self.assertEquals(str(accountType), accountType.name)

    def test_accountType_creatable_default(self):
        accountType = AccountType.objects.create(name="some_account_type")
        self.assertFalse(accountType.creatable)

    def test_account_balance_with_no_transactions(self):
        account = Account.objects.create(
            name="some_account", internal_type=InternalAccountType.personal.value)
        self.assertEquals(account.balance, 0)
