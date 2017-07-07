from django.test import TestCase
from django.urls import reverse

from pyaccountant.models import Account, InternalAccountType


class ViewTests(TestCase):
    def test_context_AccountCreate(self):
        context = self.client.get(reverse('account_new')).context
        self.assertEquals(context['menu'], 'accounts')
        self.assertEquals(context['submenu'], 'new')

    def test_context_ExpenseAccountIndex(self):
        context = self.client.get(reverse('expense_accounts')).context
        self.assertEquals(context['menu'], 'accounts')
        self.assertEquals(context['submenu'], 'expense')

    def test_context_RevenueAccountIndex(self):
        context = self.client.get(reverse('revenue_accounts')).context
        self.assertEquals(context['menu'], 'accounts')
        self.assertEquals(context['submenu'], 'revenue')

    def test_context_PersonalAccountIndex(self):
        context = self.client.get(reverse('personal_accounts')).context
        self.assertEquals(context['menu'], 'accounts')
        self.assertEquals(context['submenu'], 'personal')

    def test_context_TransactionIndex(self):
        context = self.client.get(reverse('transactions')).context
        self.assertEquals(context['menu'], 'transactions')
        self.assertEquals(context['submenu'], 'all')

    def test_context_account_TransactionIndex(self):
        account = Account.objects.create(
            name="some_account", internal_type=InternalAccountType.personal.value)
        context = self.client.get(reverse('account_transactions', args=[account.pk])).context
        self.assertEquals(context['menu'], 'transactions')
        self.assertEquals(context['submenu'], 'all')
        self.assertEquals(context['account'], account)

    def test_context_account_TransferCreate(self):
        context = self.client.get(reverse('transfer_new')).context
        self.assertEquals(context['menu'], 'transactions')
        self.assertEquals(context['submenu'], 'transfer')

    def test_context_account_DepositCreate(self):
        context = self.client.get(reverse('deposit_new')).context
        self.assertEquals(context['menu'], 'transactions')
        self.assertEquals(context['submenu'], 'deposit')

    def test_context_account_WithdrawCreate(self):
        context = self.client.get(reverse('withdraw_new')).context
        self.assertEquals(context['menu'], 'transactions')
        self.assertEquals(context['submenu'], 'withdraw')
