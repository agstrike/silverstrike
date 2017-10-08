from django.test import TestCase

from silverstrike.forms import RecurringTransactionForm
from silverstrike.models import Account, RecurringTransaction, Transaction


class RecurringTransactionFormTests(TestCase):
    def test_available_form_fields(self):
        form = RecurringTransactionForm()
        fields = ['title', 'transaction_type', 'date', 'amount',
                  'src', 'dst', 'category', 'recurrence']
        self.assertEquals(len(form.fields), len(fields))
        for field in fields:
            self.assertIn(field, form.fields)

    def test_negative_amount(self):
        personal = Account.objects.create(name='foo')
        other = Account.objects.create(name='bar')
        form = RecurringTransactionForm({
            'amount': -100, 'transaction_type': Transaction.TRANSFER, 'date': '2100-01-01',
            'src': personal, 'dst': other, 'recurrence': RecurringTransaction.MONTHLY,
            'title': 'foo'})
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 1)
        self.assertIn('amount', form.errors)

    def test_past_date(self):
        personal = Account.objects.create(name='foo')
        other = Account.objects.create(name='bar')
        form = RecurringTransactionForm({
            'amount': 100, 'transaction_type': Transaction.TRANSFER,
            'src': personal, 'dst': other, 'date': '2016-01-01',
            'recurrence': RecurringTransaction.MONTHLY, 'title': 'foo'})
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 1)
        self.assertIn('date', form.errors)

    def test_transfer_with_existing_accounts(self):
        personal = Account.objects.create(name='foo')
        other = Account.objects.create(name='bar')
        form = RecurringTransactionForm({
            'amount': 100, 'transaction_type': Transaction.TRANSFER, 'date': '2100-01-01',
            'src': personal, 'dst': other, 'recurrence': RecurringTransaction.MONTHLY,
            'title': 'foo'})
        self.assertTrue(form.is_valid())
        transaction = form.save()
        self.assertIsNotNone(transaction)
        self.assertEquals(transaction.src, personal)
        self.assertEquals(transaction.dst, other)

    def test_withdraw_with_existing_accounts(self):
        personal = Account.objects.create(name='foo')
        other = Account.objects.create(name='bar', account_type=Account.EXPENSE)
        form = RecurringTransactionForm({
            'amount': 100, 'transaction_type': Transaction.WITHDRAW, 'date': '2100-01-01',
            'src': personal, 'dst': other, 'recurrence': RecurringTransaction.MONTHLY,
            'title': 'foo'})
        self.assertTrue(form.is_valid())
        transaction = form.save()
        self.assertIsNotNone(transaction)
        self.assertEquals(transaction.src, personal)
        self.assertEquals(transaction.dst, other)

    def test_deposit_with_existing_accounts(self):
        personal = Account.objects.create(name='foo')
        other = Account.objects.create(name='bar', account_type=Account.REVENUE)
        form = RecurringTransactionForm({
            'amount': 100, 'transaction_type': Transaction.DEPOSIT, 'date': '2100-01-01',
            'src': other, 'dst': personal, 'recurrence': RecurringTransaction.MONTHLY,
            'title': 'foo'})
        self.assertTrue(form.is_valid())
        transaction = form.save()
        self.assertIsNotNone(transaction)
        self.assertEquals(transaction.src, other)
        self.assertEquals(transaction.dst, personal)
