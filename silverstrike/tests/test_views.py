from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from silverstrike.forms import DepositForm, TransferForm, WithdrawForm
from silverstrike.models import Account, TransactionJournal


class ViewTests(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin', email='email@example.com', password='pass')
        self.client.login(username='admin', password='pass')
        self.account = Account.objects.create(name="first account")
        self.personal = Account.objects.create(name="personal account")
        self.expense = Account.objects.create(
            name="expense account", account_type=Account.EXPENSE)
        self.revenue = Account.objects.create(
            name="revenue account", account_type=Account.REVENUE)

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
        context = self.client.get(self.account.get_absolute_url()).context
        self.assertEquals(context['menu'], 'accounts')
        self.assertEquals(context['submenu'], 'personal')
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

    def test_context_and_initial_TransferUpdate(self):
        form = TransferForm({
            'title': 'transaction_title',
            'source_account': self.account.pk,
            'destination_account': self.personal.pk,
            'amount': 123,
            'date': '2017-01-01',
            'transaction_type': TransactionJournal.TRANSFER
            })

        self.assertTrue(form.is_valid())
        journal = form.save()
        url = reverse('transaction_update', args=[journal.pk])
        context = self.client.get(url).context
        self.assertRedirects(self.client.post(url, {
                    'title': 'transaction_title',
                    'source_account': self.account.pk,
                    'destination_account': self.personal.pk,
                    'amount': 123,
                    'date': '2017-01-01'},
                    args=[journal.pk]), reverse('transaction_detail', args=[journal.pk]))
        self.assertEquals(context['menu'], 'transactions')
        self.assertFalse('submenu' in context)

        self.assertEquals(context['form']['title'].value(), 'transaction_title')
        self.assertEquals(context['form']['source_account'].value(), self.account.pk)
        self.assertEquals(context['form']['destination_account'].value(), self.personal.pk)
        self.assertEquals(context['form']['amount'].value(), 123)
        self.assertEquals(str(context['form']['date'].value()), '2017-01-01')

    def test_context_and_initial_WithdrawUpdate(self):
        form = WithdrawForm({
            'title': 'transaction_title',
            'source_account': self.account.pk,
            'destination_account': self.expense,
            'amount': 123,
            'date': '2017-01-01',
            'transaction_type': TransactionJournal.WITHDRAW
            })

        self.assertTrue(form.is_valid())
        journal = form.save()
        url = reverse('transaction_update', args=[journal.pk])
        context = self.client.get(url).context
        self.assertRedirects(self.client.post(url, {
                    'title': 'transaction_title',
                    'source_account': self.account.pk,
                    'destination_account': self.expense,
                    'amount': 123,
                    'date': '2017-01-01'},
                    args=[journal.pk]), reverse('transaction_detail', args=[journal.pk]))
        self.assertEquals(context['menu'], 'transactions')
        self.assertFalse('submenu' in context)

        self.assertEquals(context['form']['title'].value(), 'transaction_title')
        self.assertEquals(context['form']['source_account'].value(), self.account.pk)
        self.assertEquals(context['form']['destination_account'].value(), self.expense)
        self.assertEquals(context['form']['amount'].value(), 123)
        self.assertEquals(str(context['form']['date'].value()), '2017-01-01')

    def test_context_and_initial_DepositUpdate(self):
        form = DepositForm({
            'title': 'transaction_title',
            'source_account': self.revenue,
            'destination_account': 2,
            'amount': 123,
            'date': '2017-01-01',
            'transaction_type': TransactionJournal.DEPOSIT
            })

        self.assertTrue(form.is_valid())
        journal = form.save()
        url = reverse('transaction_update', args=[journal.pk])
        context = self.client.get(url).context
        self.assertRedirects(self.client.post(url, {
                    'title': 'transaction_title',
                    'source_account': self.revenue,
                    'destination_account': self.account.pk,
                    'amount': 123,
                    'date': '2017-01-01'},
                    args=[journal.pk]), reverse('transaction_detail', args=[journal.pk]))
        self.assertEquals(context['menu'], 'transactions')
        self.assertFalse('submenu' in context)

        self.assertEquals(context['form']['title'].value(), 'transaction_title')
        self.assertEquals(context['form']['source_account'].value(), self.revenue)
        self.assertEquals(context['form']['destination_account'].value(), self.account.pk)
        self.assertEquals(context['form']['amount'].value(), 123)
        self.assertEquals(str(context['form']['date'].value()), '2017-01-01')

    def test_context_CategoryIndex(self):
        context = self.client.get(reverse('categories')).context
        self.assertEquals(context['menu'], 'categories')
        self.assertFalse('submenu' in context)

    def test_context_IndexView(self):
        context = self.client.get(reverse('index')).context
        self.assertEquals(context['menu'], 'home')

    def test_get_account_info(self):
        # TODO
        pass

    def test_ChartView(self):
        # TODO
        self.client.get(reverse('charts'))

    def test_api_accounts_balance(self):
        # TODO
        self.client.get(reverse('api_accounts_balance', args=['2017-01-01', '2017-06-01']))
