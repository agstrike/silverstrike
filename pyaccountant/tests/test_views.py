from django.test import TestCase
from django.urls import reverse

from pyaccountant.forms import TransferForm
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

    def test_context_TransferCreate(self):
        context = self.client.get(reverse('transfer_new')).context
        self.assertEquals(context['menu'], 'transactions')
        self.assertEquals(context['submenu'], 'transfer')

    def test_context_DepositCreate(self):
        context = self.client.get(reverse('deposit_new')).context
        self.assertEquals(context['menu'], 'transactions')
        self.assertEquals(context['submenu'], 'deposit')

    def test_context_WithdrawCreate(self):
        context = self.client.get(reverse('withdraw_new')).context
        self.assertEquals(context['menu'], 'transactions')
        self.assertEquals(context['submenu'], 'withdraw')

    def test_context_and_initial_TransactionUpdate(self):
        Account.objects.create(
            name="first account", internal_type=InternalAccountType.personal.value)
        Account.objects.create(
            name="second account", internal_type=InternalAccountType.personal.value)

        form = TransferForm({
            'title': 'transaction_title',
            'source_account': 1,
            'destination_account': 2,
            'amount': 123,
            'date': '2017-01-01'
            })

        self.assertTrue(form.is_valid())
        journal = form.save()
        context = self.client.get(reverse('transaction_edit', args=[journal.pk])).context
        self.assertEquals(context['menu'], 'transactions')
        self.assertFalse('submenu' in context)

        self.assertEquals(context['form']['title'].value(), 'transaction_title')
        self.assertEquals(context['form']['source_account'].value(), 1)
        self.assertEquals(context['form']['destination_account'].value(), 2)
        self.assertEquals(context['form']['amount'].value(), 123)
        self.assertEquals(str(context['form']['date'].value()), '2017-01-01')
