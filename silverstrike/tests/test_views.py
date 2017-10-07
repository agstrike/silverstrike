from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from silverstrike.forms import DepositForm, TransferForm, WithdrawForm
from silverstrike.models import Account, Transaction


class ViewTests(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin', email='email@example.com', password='pass')
        self.client.login(username='admin', password='pass')
        self.account = Account.objects.create(name='first account', show_on_dashboard=True)
        self.personal = Account.objects.create(name='personal account')
        self.expense = Account.objects.create(
            name="expense account", account_type=Account.EXPENSE)
        self.revenue = Account.objects.create(
            name="revenue account", account_type=Account.REVENUE)

    def test_context_AccountCreate(self):
        context = self.client.get(reverse('account_new')).context
        self.assertEquals(context['menu'], 'accounts')

    def test_context_AccountIndex(self):
        context = self.client.get(reverse('accounts')).context
        self.assertEquals(context['menu'], 'accounts')
        self.assertEquals(len(context['accounts']), 2)
        self.assertEquals(self.account.id, context['accounts'][0]['id'])
        self.assertEquals(self.account.name, context['accounts'][0]['name'])
        self.assertEquals(self.account.active, context['accounts'][0]['active'])

    def test_context_TransactionIndex(self):
        context = self.client.get(reverse('transactions')).context
        self.assertEquals(context['menu'], 'transactions')
        self.assertEquals(context['submenu'], 'all')

    def test_context_account_TransactionIndex(self):
        context = self.client.get(self.account.get_absolute_url()).context
        self.assertEquals(context['menu'], 'accounts')
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
            'transaction_type': Transaction.TRANSFER
            })

        self.assertTrue(form.is_valid())
        transaction = form.save()
        url = reverse('transaction_update', args=[transaction.pk])
        context = self.client.get(url).context
        self.assertRedirects(self.client.post(url, {
                    'title': 'transaction_title',
                    'source_account': self.account.pk,
                    'destination_account': self.personal.pk,
                    'amount': 123,
                    'date': '2017-01-01'},
                    args=[transaction.pk]), reverse('transaction_detail', args=[transaction.pk]))
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
            'transaction_type': Transaction.WITHDRAW
            })

        self.assertTrue(form.is_valid())
        transaction = form.save()
        url = reverse('transaction_update', args=[transaction.pk])
        context = self.client.get(url).context
        self.assertRedirects(self.client.post(url, {
                    'title': 'transaction_title',
                    'source_account': self.account.pk,
                    'destination_account': self.expense,
                    'amount': 123,
                    'date': '2017-01-01'},
                    args=[transaction.pk]), reverse('transaction_detail', args=[transaction.pk]))
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
            'transaction_type': Transaction.DEPOSIT
            })

        self.assertTrue(form.is_valid())
        transaction = form.save()
        url = reverse('transaction_update', args=[transaction.pk])
        context = self.client.get(url).context
        self.assertRedirects(self.client.post(url, {
                    'title': 'transaction_title',
                    'source_account': self.revenue,
                    'destination_account': self.account.pk,
                    'amount': 123,
                    'date': '2017-01-01'},
                    args=[transaction.pk]), reverse('transaction_detail', args=[transaction.pk]))
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


    def test_personal_AccountUpdateView(self):
        context = self.client.get(reverse('account_update', args=[self.account.id])).context
        self.assertIn('name', context['form'].fields)
        self.assertIn('show_on_dashboard', context['form'].fields)
        self.assertIn('active', context['form'].fields)

    def test_revenue_AccountUpdateView(self):
        context = self.client.get(reverse('account_update', args=[self.revenue.id])).context
        self.assertIn('name', context['form'].fields)
        self.assertNotIn('show_on_dashboard', context['form'].fields)
        self.assertNotIn('active', context['form'].fields)

    def test_expense_AccountUpdateView(self):
        context = self.client.get(reverse('account_update', args=[self.expense.id])).context
        self.assertIn('name', context['form'].fields)
        self.assertNotIn('show_on_dashboard', context['form'].fields)
        self.assertNotIn('active', context['form'].fields)

    def test_system_AccountUpdateView(self):
        system = Account.objects.get(account_type=Account.SYSTEM)
        response = self.client.get(reverse('account_update', args=[system.id]))
        self.assertEquals(response.status_code, 404)