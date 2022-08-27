from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from silverstrike.forms import DepositForm, TransferForm, WithdrawForm
from silverstrike.models import Account, AccountType, Transaction


class ViewTests(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin', email='email@example.com', password='pass')
        self.client.login(username='admin', password='pass')
        self.account = Account.objects.create(name='first account', show_on_dashboard=True)
        self.personal = Account.objects.create(name='personal account')
        self.expense = Account.objects.create(
            name="expense account", account_type=AccountType.FOREIGN)
        self.revenue = Account.objects.create(
            name="revenue account", account_type=AccountType.FOREIGN)

    def test_context_TransactionIndex(self):
        context = self.client.get(reverse('transactions')).context
        self.assertEqual(context['menu'], 'transactions')
        self.assertEqual(context['submenu'], 'all')

    def test_context_account_TransactionIndex(self):
        context = self.client.get(self.account.get_absolute_url()).context
        self.assertEqual(context['menu'], 'accounts')
        self.assertEqual(context['account'], self.account)

    def test_context_TransferCreate(self):
        context = self.client.get(reverse('transfer_new')).context
        self.assertEqual(context['menu'], 'transactions')
        self.assertEqual(context['submenu'], 'transfer')

    def test_context_DepositCreate(self):
        context = self.client.get(reverse('deposit_new')).context
        self.assertEqual(context['menu'], 'transactions')
        self.assertEqual(context['submenu'], 'deposit')

    def test_context_WithdrawCreate(self):
        context = self.client.get(reverse('withdraw_new')).context
        self.assertEqual(context['menu'], 'transactions')
        self.assertEqual(context['submenu'], 'withdraw')

    def test_context_and_initial_TransferUpdate(self):
        form = TransferForm({
            'title': 'transaction_title',
            'src': self.account.pk,
            'dst': self.personal.pk,
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
                    'src': self.account.pk,
                    'dst': self.personal.pk,
                    'amount': 123,
                    'date': '2017-01-01'},
                    args=[transaction.pk]), reverse('transaction_detail', args=[transaction.pk]))
        self.assertEqual(context['menu'], 'transactions')
        self.assertFalse('submenu' in context)

        self.assertEqual(context['form']['title'].value(), 'transaction_title')
        self.assertEqual(context['form']['src'].value(), self.account.pk)
        self.assertEqual(context['form']['dst'].value(), self.personal.pk)
        self.assertEqual(context['form']['amount'].value(), 123)
        self.assertEqual(str(context['form']['date'].value()), '2017-01-01')

    def test_context_and_initial_WithdrawUpdate(self):
        form = WithdrawForm({
            'title': 'transaction_title',
            'src': self.account.pk,
            'dst': self.expense,
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
                    'src': self.account.pk,
                    'dst': self.expense,
                    'amount': 123,
                    'date': '2017-01-01'},
                    args=[transaction.pk]), reverse('transaction_detail', args=[transaction.pk]))
        self.assertEqual(context['menu'], 'transactions')
        self.assertFalse('submenu' in context)

        self.assertEqual(context['form']['title'].value(), 'transaction_title')
        self.assertEqual(context['form']['src'].value(), self.account.pk)
        self.assertEqual(context['form']['dst'].value(), self.expense)
        self.assertEqual(context['form']['amount'].value(), 123)
        self.assertEqual(str(context['form']['date'].value()), '2017-01-01')

    def test_context_and_initial_DepositUpdate(self):
        form = DepositForm({
            'title': 'transaction_title',
            'src': self.revenue.name,
            'dst': self.account.id,
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
                    'src': self.revenue,
                    'dst': self.account.pk,
                    'amount': 123,
                    'date': '2017-01-01'},
                    args=[transaction.pk]), reverse('transaction_detail', args=[transaction.pk]))
        self.assertEqual(context['menu'], 'transactions')
        self.assertFalse('submenu' in context)

        self.assertEqual(context['form']['title'].value(), 'transaction_title')
        self.assertEqual(context['form']['src'].value(), self.revenue)
        self.assertEqual(context['form']['dst'].value(), self.account.pk)
        self.assertEqual(context['form']['amount'].value(), 123)
        self.assertEqual(str(context['form']['date'].value()), '2017-01-01')
