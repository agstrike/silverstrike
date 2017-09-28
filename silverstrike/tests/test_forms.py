from django.db import models
from django.test import TestCase

from silverstrike.forms import DepositForm, TransferForm, WithdrawForm
from silverstrike.models import Account, Split, Transaction


class FormTests(TestCase):
    def setUp(self):
        self.account = Account.objects.create(name="first account")
        self.personal = Account.objects.create(name="personal account")

    def test_TransferForm(self):
        data = {
            'title': 'transfer',
            'source_account': self.account.pk,
            'destination_account': self.personal.pk,
            'amount': 123,
            'date': '2017-01-01'
            }
        form = TransferForm(data)
        self.assertTrue(form.is_valid())
        transfer = form.save()
        self.assertIsInstance(transfer, Transaction)
        self.assertEquals(len(Account.objects.all()), 3)  # Sytem account is also present
        self.assertEquals(len(Transaction.objects.all()), 1)
        self.assertEquals(len(Split.objects.all()), 2)
        self.assertEquals(Split.objects.all().aggregate(
            models.Sum('amount'))['amount__sum'], 0)
        self.assertTrue(Split.objects.get(
            account=self.personal, opposing_account=self.account, amount=123).is_transfer)
        self.assertTrue(Split.objects.get(
            account=self.account, opposing_account=self.personal, amount=-123).is_transfer)

    def test_DepositForm(self):
        data = {
            'title': 'deposit',
            'source_account': 'Work account',
            'destination_account': self.account.pk,
            'amount': 123,
            'date': '2017-01-01'
            }
        for i in range(1, 3):
            form = DepositForm(data)
            self.assertTrue(form.is_valid())
            transaction = form.save()
            self.assertIsInstance(transaction, Transaction)
            self.assertEquals(len(Transaction.objects.all()), i)
            self.assertEquals(len(Split.objects.all()), 2 * i)
            self.assertEquals(len(Account.objects.all()), 4)  # System account is also present
            self.assertEquals(len(Account.objects.filter(
                account_type=Account.REVENUE)), 1)
            new_account = Account.objects.get(
                account_type=Account.REVENUE)
            self.assertEquals(Split.objects.all().aggregate(
                models.Sum('amount'))['amount__sum'], 0)
            self.assertTrue(
                Split.objects.get(account=new_account, opposing_account_id=self.account.pk,
                                  amount=-123, transaction=transaction).is_deposit)
            self.assertTrue(
                Split.objects.get(account_id=self.account.pk, opposing_account=new_account,
                                  amount=123, transaction=transaction).is_deposit)

    def test_WithdrawForm(self):
        data = {
            'title': 'withdraw',
            'source_account': self.account.pk,
            'destination_account': 'Supermarket a',
            'amount': 123,
            'date': '2017-01-01'
            }
        for i in range(1, 3):
            form = WithdrawForm(data)
            self.assertTrue(form.is_valid())
            transaction = form.save()
            self.assertIsInstance(transaction, Transaction)
            self.assertEquals(len(Transaction.objects.all()), i)
            self.assertEquals(len(Split.objects.all()), 2 * i)
            self.assertEquals(len(Account.objects.all()), 4)  # System account is also present
            self.assertEquals(len(Account.objects.filter(
                account_type=Account.EXPENSE)), 1)
            new_account = Account.objects.get(
                account_type=Account.EXPENSE)
            self.assertTrue(
                Split.objects.get(account_id=self.account.pk, opposing_account=new_account,
                                  amount=-123, transaction=transaction).is_withdraw)
            self.assertTrue(
                Split.objects.get(account=new_account, opposing_account_id=self.account.pk,
                                  amount=123, transaction=transaction).is_withdraw)
            self.assertEquals(Split.objects.all().aggregate(
                models.Sum('amount'))['amount__sum'], 0)

    def test_different_revenue_accounts(self):
        data = {
            'title': 'deposit',
            'source_account': 'Job a',
            'destination_account': self.account.pk,
            'amount': 123,
            'date': '2017-01-01',
            'transaction_type': Transaction.DEPOSIT,
            }
        form = DepositForm(data)
        self.assertTrue(form.is_valid())
        form.save()
        data['source_account'] = 'Job b'
        form = DepositForm(data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEquals(len(Account.objects.filter(
            account_type=Account.REVENUE)), 2)

    def test_different_expense_accounts(self):
        data = {
            'title': 'withdraw',
            'source_account': self.account.pk,
            'destination_account': 'Supermarket a',
            'amount': 123,
            'date': '2017-01-01'
            }
        form = WithdrawForm(data)
        self.assertTrue(form.is_valid())
        form.save()
        data['destination_account'] = 'Supermarket b'
        form = WithdrawForm(data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEquals(len(Account.objects.filter(
            account_type=Account.EXPENSE)), 2)

    def test_transfer_to_same_account(self):
        data = {
            'title': 'transfer',
            'source_account': self.account.pk,
            'destination_account': self.account.pk,
            'amount': 123,
            'date': '2017-01-01',
            'transaction_type': Transaction.TRANSFER
            }
        form = TransferForm(data)
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 2)
        self.assertEquals(len(form.errors['source_account']), 1)
        self.assertEquals(len(form.errors['destination_account']), 1)

    def test_transfer_form_only_shows_personal_accounts(self):
        pass
