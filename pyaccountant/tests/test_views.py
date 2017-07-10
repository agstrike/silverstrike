from django.test import TestCase
from django.urls import reverse

from pyaccountant.forms import TransferForm
from pyaccountant.models import Account, InternalAccountType


class ViewTests(TestCase):
    def setUp(self):
        self.account = Account.objects.create(
            name="first account", internal_type=InternalAccountType.personal.value)
        self.personal = Account.objects.create(
            name="personal account", internal_type=InternalAccountType.personal.value)
        self.expense = Account.objects.create(
            name="expense account", internal_type=InternalAccountType.expense.value)
        self.revenue = Account.objects.create(
            name="revenue account", internal_type=InternalAccountType.revenue.value)

    def test_context_AccountCreate(self):
        context = self.client.get(reverse('account_new')).context
        self.assertEquals(context['menu'], 'accounts')
        self.assertEquals(context['submenu'], 'new')

    def test_context_ExpenseAccountIndex(self):
        context = self.client.get(reverse('expense_accounts')).context
        self.assertEquals(context['menu'], 'accounts')
        self.assertEquals(context['submenu'], 'expense')
        self.assertEquals(len(context['accounts']), 1)
        self.assertEquals(context['accounts'][0], self.expense)

    def test_context_RevenueAccountIndex(self):
        context = self.client.get(reverse('revenue_accounts')).context
        self.assertEquals(context['menu'], 'accounts')
        self.assertEquals(context['submenu'], 'revenue')
        self.assertEquals(len(context['accounts']), 1)
        self.assertEquals(context['accounts'][0], self.revenue)

    def test_context_PersonalAccountIndex(self):
        context = self.client.get(reverse('personal_accounts')).context
        self.assertEquals(context['menu'], 'accounts')
        self.assertEquals(context['submenu'], 'personal')
        self.assertEquals(len(context['accounts']), 2)
        self.assertIn(self.personal, context['accounts'])
        self.assertIn(self.account, context['accounts'])

    def test_context_TransactionIndex(self):
        context = self.client.get(reverse('transactions')).context
        self.assertEquals(context['menu'], 'transactions')
        self.assertEquals(context['submenu'], 'all')

    def test_context_account_TransactionIndex(self):
        context = self.client.get(reverse('account_transactions', args=[self.account.pk])).context
        self.assertEquals(context['menu'], 'transactions')
        self.assertEquals(context['submenu'], 'all')
        self.assertEquals(context['account'], self.account)

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

    def test_context_IndexView(self):
        context = self.client.get(reverse('index')).context
        self.assertEquals(context['menu'], 'home')
