from django.db import models
from django.test import TestCase

from silverstrike.forms import (RecurringDepositForm, RecurringTransactionForm,
                                RecurringTransferForm, RecurringWithdrawForm)
from silverstrike.models import Account, RecurringSplit, RecurringTransaction


class RecurringTransactionFormTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='personal')
        self.savings = Account.objects.create(name='savings')
        self.foreign = Account.objects.create(name='foreign',
                                              account_type=Account.FOREIGN)
        self.other_foreign = Account.objects.create(name='other foreign',
                                                    account_type=Account.FOREIGN)

    def test_available_form_fields(self):
        form = RecurringTransactionForm()
        fields = ['title', 'date', 'amount', 'source_account',
                  'destination_account', 'category', 'notes', 'interval',
                  'multiplier', 'weekend_handling']
        self.assertEqual(len(form.fields), len(fields))
        for field in fields:
            self.assertIn(field, form.fields)

    def test_negative_amount(self):
        form = RecurringTransactionForm({
            'amount': -100, 'date': '2100-01-01', 'multiplier': 1,
            'source_account': self.personal.id, 'title': 'foo',
            'destination_account': self.savings.id,
            'interval': RecurringTransaction.MONTHLY,
            'weekend_handling': RecurringTransaction.SKIP})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertIn('amount', form.errors)

    def test_positive_less_than_minimum(self):
        form = RecurringTransactionForm({
            'amount': .001, 'date': '2100-01-01', 'multiplier': 1,
            'source_account': self.personal.id,
            'destination_account': self.savings.id,
            'interval': RecurringTransaction.MONTHLY, 'title': 'foo',
            'weekend_handling': RecurringTransaction.SKIP})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertIn('amount', form.errors)

    def test_past_date(self):
        form = RecurringTransactionForm({
            'amount': 100, 'multiplier': 1,
            'weekend_handling': RecurringTransaction.SKIP,
            'source_account': self.personal.id,
            'destination_account': self.savings.id, 'date': '2016-01-01',
            'interval': RecurringTransaction.MONTHLY, 'title': 'foo'})
        self.assertTrue(form.is_valid())

    def test_RecurringDepositForm(self):
        for i in range(1, 3):
            form = RecurringDepositForm({
                'amount': 100, 'date': '2100-01-01', 'multiplier': 1,
                'source_account': 'new foreign account',
                'destination_account': self.personal.id,
                'interval': RecurringTransaction.MONTHLY,
                'title': 'foo', 'weekend_handling': RecurringTransaction.SKIP})
            self.assertTrue(form.is_valid())
            form.clean()
            deposit = form.save()
            self.assertIsInstance(deposit, RecurringTransaction)
            self.assertEqual(len(RecurringTransaction.objects.all()), i)
            self.assertEqual(len(RecurringSplit.objects.all()), 2 * i)
            self.assertEqual(len(Account.objects.all()), 6)  # System account is also present
            self.assertTrue(deposit.is_deposit)
            self.assertEqual(len(deposit.splits.income()), 1)
            self.assertEqual(deposit.splits.income().first().opposing_account,
                             Account.objects.filter(name='new foreign account').first())
            self.assertEqual(Account.objects.filter(
                name='new foreign account').first().account_type,
                Account.FOREIGN)
            self.assertEqual(RecurringSplit.objects.all().aggregate(
                models.Sum('amount'))['amount__sum'], 0)
            for split in deposit.splits.all():
                self.assertTrue(split.is_deposit)

    def test_RecurringWithdrawForm(self):
        for i in range(1, 3):
            form = RecurringWithdrawForm({
                'amount': 100, 'date': '2100-01-01', 'multiplier': 1,
                'source_account': self.personal.id,
                'destination_account': 'new foreign account',
                'interval': RecurringTransaction.MONTHLY,
                'title': 'foo', 'weekend_handling': RecurringTransaction.SKIP})
            self.assertTrue(form.is_valid())
            form.clean()
            withdraw = form.save()
            self.assertIsInstance(withdraw, RecurringTransaction)
            self.assertEqual(len(RecurringTransaction.objects.all()), i)
            self.assertEqual(len(RecurringSplit.objects.all()), 2 * i)
            self.assertEqual(len(Account.objects.all()), 6)  # System account is also present
            self.assertTrue(withdraw.is_withdraw)
            self.assertEqual(len(withdraw.splits.expense()), 1)
            self.assertEqual(withdraw.splits.expense().first().opposing_account,
                             Account.objects.filter(name='new foreign account').first())
            self.assertEqual(Account.objects.filter(
                name='new foreign account').first().account_type,
                Account.FOREIGN)
            self.assertEqual(RecurringSplit.objects.all().aggregate(
                models.Sum('amount'))['amount__sum'], 0)
            for split in withdraw.splits.all():
                self.assertTrue(split.is_withdraw)

    def test_RecurringTransferForm(self):
        form = RecurringTransferForm({
            'amount': 100, 'date': '2100-01-01', 'multiplier': 1,
            'source_account': self.personal.id,
            'destination_account': self.savings.id,
            'interval': RecurringTransaction.MONTHLY,
            'title': 'foo', 'weekend_handling': RecurringTransaction.SKIP})
        self.assertTrue(form.is_valid())
        form.clean()
        transfer = form.save()
        self.assertIsInstance(transfer, RecurringTransaction)
        self.assertEqual(len(RecurringTransaction.objects.all()), 1)
        self.assertEqual(len(RecurringSplit.objects.all()), 2)
        self.assertEqual(len(Account.objects.all()), 5)  # System account is also present
        self.assertTrue(transfer.is_transfer)
        self.assertEqual(len(transfer.splits.transfers_once()), 1)
        self.assertEqual(RecurringSplit.objects.all().aggregate(
            models.Sum('amount'))['amount__sum'], 0)
        for split in transfer.splits.all():
            self.assertTrue(split.is_transfer)
