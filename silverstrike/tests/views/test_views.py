from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from silverstrike.forms import (DepositForm, RecurringDepositForm,
                                RecurringTransferForm, RecurringWithdrawForm, TransferForm,
                                WithdrawForm)
from silverstrike.models import Account, RecurringTransaction, Transaction


class ViewTests(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin', email='email@example.com', password='pass')
        self.client.login(username='admin', password='pass')
        self.account = Account.objects.create(name='first account', show_on_dashboard=True)
        self.personal = Account.objects.create(name='personal account')
        self.expense = Account.objects.create(
            name="expense account", account_type=Account.FOREIGN)
        self.revenue = Account.objects.create(
            name="revenue account", account_type=Account.FOREIGN)

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
        self.assertEqual(context['menu'], 'transactions')
        self.assertFalse('submenu' in context)

        self.assertEqual(context['form']['title'].value(), 'transaction_title')
        self.assertEqual(context['form']['source_account'].value(), self.account.pk)
        self.assertEqual(context['form']['destination_account'].value(), self.personal.pk)
        self.assertEqual(context['form']['amount'].value(), 123)
        self.assertEqual(str(context['form']['date'].value()), '2017-01-01')

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
        self.assertEqual(context['menu'], 'transactions')
        self.assertFalse('submenu' in context)

        self.assertEqual(context['form']['title'].value(), 'transaction_title')
        self.assertEqual(context['form']['source_account'].value(), self.account.pk)
        self.assertEqual(context['form']['destination_account'].value(), self.expense)
        self.assertEqual(context['form']['amount'].value(), 123)
        self.assertEqual(str(context['form']['date'].value()), '2017-01-01')

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
        self.assertEqual(context['menu'], 'transactions')
        self.assertFalse('submenu' in context)

        self.assertEqual(context['form']['title'].value(), 'transaction_title')
        self.assertEqual(context['form']['source_account'].value(), self.revenue)
        self.assertEqual(context['form']['destination_account'].value(), self.account.pk)
        self.assertEqual(context['form']['amount'].value(), 123)
        self.assertEqual(str(context['form']['date'].value()), '2017-01-01')

    def test_context_CategoryIndex(self):
        context = self.client.get(reverse('categories')).context
        self.assertEqual(context['menu'], 'categories')
        self.assertFalse('submenu' in context)

    def test_context_RecurringTransactionIndex(self):
        context = self.client.get(reverse('recurrences')).context
        self.assertEqual(context['menu'], 'recurrences')
        self.assertEqual(context['submenu'], 'all')

    def test_context_RecurringTransferCreate(self):
        context = self.client.get(reverse('recurring_transfer_new')).context
        self.assertEqual(context['menu'], 'transactions')
        self.assertEqual(context['submenu'], 'transfer')

    def test_context_RecurringDepositCreate(self):
        context = self.client.get(reverse('recurring_deposit_new')).context
        self.assertEqual(context['menu'], 'transactions')
        self.assertEqual(context['submenu'], 'deposit')

    def test_context_RecurringWithdrawCreate(self):
        context = self.client.get(reverse('recurring_withdraw_new')).context
        self.assertEqual(context['menu'], 'transactions')
        self.assertEqual(context['submenu'], 'withdraw')

    def test_context_and_initial_RecurringTransferUpdate(self):
        form = RecurringTransferForm({
            'amount': 123, 'date': '2017-01-01', 'skip': 0,
            'source_account': self.account.pk,
            'destination_account': self.personal.pk,
            'recurrence': RecurringTransaction.MONTHLY,
            'title': 'foo', 'weekend_handling': RecurringTransaction.SKIP})

        self.assertTrue(form.is_valid())
        transfer = form.save()
        url = reverse('recurrence_update', args=[transfer.pk])
        context = self.client.get(url).context
        self.assertRedirects(self.client.post(url,
                                              {'title': 'foo',
                                               'source_account': self.account.pk,
                                               'destination_account': self.personal.pk,
                                               'amount': 123,
                                               'date': '2017-01-01',
                                               'recurrence': RecurringTransaction.MONTHLY,
                                               'weekend_handling': RecurringTransaction.SKIP,
                                               'skip': 0},
                                              args=[transfer.pk]),
                             reverse('recurrence_detail',
                                     args=[transfer.pk]))
        self.assertEqual(context['menu'], 'recurrences')
        self.assertFalse('submenu' in context)

        self.assertEqual(context['form']['title'].value(), 'foo')
        self.assertEqual(context['form']['source_account'].value(), self.account.pk)
        self.assertEqual(context['form']['destination_account'].value(), self.personal.pk)
        self.assertEqual(context['form']['amount'].value(), 123)
        self.assertEqual(str(context['form']['date'].value()), '2017-01-01')

    def test_context_and_initial_RecurringWithdrawUpdate(self):
        form = RecurringWithdrawForm({
            'amount': 123, 'date': '2017-01-01', 'skip': 0,
            'source_account': self.account.pk,
            'destination_account': self.expense,
            'recurrence': RecurringTransaction.MONTHLY,
            'title': 'foo', 'weekend_handling': RecurringTransaction.SKIP})

        self.assertTrue(form.is_valid())
        withdraw = form.save()
        url = reverse('recurrence_update', args=[withdraw.pk])
        context = self.client.get(url).context
        self.assertRedirects(self.client.post(url,
                                              {'title': 'foo',
                                               'source_account': self.account.pk,
                                               'destination_account': self.expense,
                                               'amount': 123,
                                               'date': '2017-01-01',
                                               'recurrence': RecurringTransaction.MONTHLY,
                                               'weekend_handling': RecurringTransaction.SKIP,
                                               'skip': 0},
                                              args=[withdraw.pk]),
                             reverse('recurrence_detail',
                                     args=[withdraw.pk]))
        self.assertEqual(context['menu'], 'recurrences')
        self.assertFalse('submenu' in context)

        self.assertEqual(context['form']['title'].value(), 'foo')
        self.assertEqual(context['form']['source_account'].value(), self.account.pk)
        self.assertEqual(context['form']['destination_account'].value(), self.expense)
        self.assertEqual(context['form']['amount'].value(), 123)
        self.assertEqual(str(context['form']['date'].value()), '2017-01-01')

    def test_context_and_initial_RecurringDepositUpdate(self):
        form = RecurringDepositForm({
            'amount': 123, 'date': '2017-01-01', 'skip': 0,
            'source_account': self.revenue,
            'destination_account': self.account.pk,
            'recurrence': RecurringTransaction.MONTHLY,
            'title': 'foo', 'weekend_handling': RecurringTransaction.SKIP})

        self.assertTrue(form.is_valid())
        deposit = form.save()
        url = reverse('recurrence_update', args=[deposit.pk])
        context = self.client.get(url).context
        self.assertRedirects(self.client.post(url,
                                              {'title': 'foo',
                                               'source_account': self.revenue,
                                               'destination_account': self.account.pk,
                                               'amount': 123,
                                               'date': '2017-01-01',
                                               'recurrence': RecurringTransaction.MONTHLY,
                                               'weekend_handling': RecurringTransaction.SKIP,
                                               'skip': 0},
                                              args=[deposit.pk]),
                             reverse('recurrence_detail',
                                     args=[deposit.pk]))
        self.assertEqual(context['menu'], 'recurrences')
        self.assertFalse('submenu' in context)

        self.assertEqual(context['form']['title'].value(), 'foo')
        self.assertEqual(context['form']['source_account'].value(), self.revenue)
        self.assertEqual(context['form']['destination_account'].value(), self.account.pk)
        self.assertEqual(context['form']['amount'].value(), 123)
        self.assertEqual(str(context['form']['date'].value()), '2017-01-01')
