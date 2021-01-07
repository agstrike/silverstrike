from django.test import TestCase

from silverstrike.forms import RecurringTransactionForm
from silverstrike.models import Account, RecurringTransaction, Transaction


class RecurringTransactionFormTests(TestCase):
    def test_available_form_fields(self):
        form = RecurringTransactionForm()
        fields = ['title', 'date', 'amount',
                  'src', 'dst', 'category', 'interval',
                  'multiplier', 'weekend_handling', 'usual_month_day']
        self.assertEqual(len(form.fields), len(fields))
        for field in fields:
            self.assertIn(field, form.fields)

    def test_negative_amount(self):
        personal = Account.objects.create(name='foo')
        other = Account.objects.create(name='bar')
        form = RecurringTransactionForm({
            'amount': -100, 'date': '2100-01-01', 'multiplier': 1,
            'src': personal.id, 'dst': other.id, 'interval': RecurringTransaction.MONTHLY,
            'title': 'foo', 'weekend_handling': RecurringTransaction.SKIP, 'usual_month_day': 0})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertIn('amount', form.errors)

    def test_past_date(self):
        personal = Account.objects.create(name='foo')
        other = Account.objects.create(name='bar')
        form = RecurringTransactionForm({
            'amount': 100, 'multiplier': 1, 'weekend_handling': RecurringTransaction.SKIP,
            'src': personal.id, 'dst': other.id, 'date': '2016-01-01',
            'interval': RecurringTransaction.MONTHLY, 'title': 'foo', 'usual_month_day': 0})
        self.assertTrue(form.is_valid())

    def test_transfer(self):
        personal = Account.objects.create(name='foo')
        other = Account.objects.create(name='bar')
        form = RecurringTransactionForm({
            'amount': 100, 'date': '2100-01-01', 'multiplier': 1,
            'src': personal.id, 'dst': other.id, 'interval': RecurringTransaction.MONTHLY,
            'title': 'foo', 'weekend_handling': RecurringTransaction.SKIP, 'usual_month_day': 0})
        self.assertTrue(form.is_valid())
        transaction = form.save()
        self.assertEqual(transaction.transaction_type, Transaction.TRANSFER)
        self.assertIsNotNone(transaction)

    def test_withdraw(self):
        personal = Account.objects.create(name='foo')
        other = Account.objects.create(name='bar', account_type=Account.AccountType.FOREIGN)
        form = RecurringTransactionForm({
            'amount': 100, 'date': '2100-01-01', 'multiplier': 1,
            'src': personal.id, 'dst': other.id, 'interval': RecurringTransaction.MONTHLY,
            'title': 'foo', 'weekend_handling': RecurringTransaction.SKIP, 'usual_month_day': 0})
        self.assertTrue(form.is_valid())
        transaction = form.save()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.transaction_type, Transaction.WITHDRAW)

    def test_deposit(self):
        personal = Account.objects.create(name='foo')
        other = Account.objects.create(name='bar', account_type=Account.AccountType.FOREIGN)
        form = RecurringTransactionForm({
            'amount': 100, 'date': '2100-01-01', 'multiplier': 1,
            'src': other.id, 'dst': personal.id, 'interval': RecurringTransaction.MONTHLY,
            'title': 'foo', 'weekend_handling': RecurringTransaction.SKIP, 'usual_month_day': 0})
        self.assertTrue(form.is_valid())
        transaction = form.save()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.transaction_type, Transaction.DEPOSIT)

    def test_two_foreign_accounts(self):
        first = Account.objects.create(name='foo', account_type=Account.AccountType.FOREIGN)
        other = Account.objects.create(name='bar', account_type=Account.AccountType.FOREIGN)
        form = RecurringTransactionForm({
            'amount': 100, 'date': '2100-01-01', 'multiplier': 1,
            'src': other.id, 'dst': first.id, 'interval': RecurringTransaction.MONTHLY,
            'title': 'foo', 'weekend_handling': RecurringTransaction.SKIP, 'usual_month_day': 0})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
