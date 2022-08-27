from django.db import models
from django.test import TestCase

from silverstrike.forms import DepositForm, TransferForm, WithdrawForm
from silverstrike.models import Account, AccountType, Split, Transaction


class FormTests(TestCase):
    def setUp(self):
        self.account = Account.objects.create(name="first account")
        self.personal = Account.objects.create(name="personal account")

    def test_TransferForm(self):
        data = {
            'title': 'transfer',
            'src': self.account.pk,
            'dst': self.personal.pk,
            'amount': 123,
            'date': '2017-01-01'
            }
        form = TransferForm(data)
        self.assertTrue(form.is_valid())
        transfer = form.save()
        self.assertIsInstance(transfer, Transaction)
        self.assertEqual(len(Account.objects.all()), 3)  # System account is also present
        self.assertEqual(len(Transaction.objects.all()), 1)
        self.assertEqual(len(Split.objects.all()), 2)
        self.assertEqual(Split.objects.all().aggregate(
            models.Sum('amount'))['amount__sum'], 0)
        self.assertTrue(Split.objects.get(
            account=self.personal, opposing_account=self.account, amount=123).is_transfer)
        self.assertTrue(Split.objects.get(
            account=self.account, opposing_account=self.personal, amount=-123).is_transfer)

    def test_DepositForm(self):
        data = {
            'title': 'deposit',
            'src': 'Work account',
            'dst': self.account.pk,
            'amount': 123,
            'date': '2017-01-01'
            }
        for i in range(1, 3):
            form = DepositForm(data)
            self.assertTrue(form.is_valid())
            transaction = form.save()
            self.assertIsInstance(transaction, Transaction)
            self.assertEqual(len(Transaction.objects.all()), i)
            self.assertEqual(len(Split.objects.all()), 2 * i)
            self.assertEqual(len(Account.objects.all()), 4)  # System account is also present
            self.assertEqual(len(Account.objects.filter(
                account_type=AccountType.FOREIGN)), 1)
            new_account = Account.objects.get(
                account_type=AccountType.FOREIGN)
            self.assertEqual(Split.objects.all().aggregate(
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
            'src': self.account.pk,
            'dst': 'Supermarket a',
            'amount': 123,
            'date': '2017-01-01'
            }
        for i in range(1, 3):
            form = WithdrawForm(data)
            self.assertTrue(form.is_valid())
            transaction = form.save()
            self.assertIsInstance(transaction, Transaction)
            self.assertEqual(len(Transaction.objects.all()), i)
            self.assertEqual(len(Split.objects.all()), 2 * i)
            self.assertEqual(len(Account.objects.all()), 4)  # System account is also present
            self.assertEqual(len(Account.objects.filter(
                account_type=AccountType.FOREIGN)), 1)
            new_account = Account.objects.get(
                account_type=AccountType.FOREIGN)
            self.assertTrue(
                Split.objects.get(account_id=self.account.pk, opposing_account=new_account,
                                  amount=-123, transaction=transaction).is_withdraw)
            self.assertTrue(
                Split.objects.get(account=new_account, opposing_account_id=self.account.pk,
                                  amount=123, transaction=transaction).is_withdraw)
            self.assertEqual(Split.objects.all().aggregate(
                models.Sum('amount'))['amount__sum'], 0)

    def test_different_revenue_accounts(self):
        data = {
            'title': 'deposit',
            'src': 'Job a',
            'dst': self.account.pk,
            'amount': 123,
            'date': '2017-01-01',
            'transaction_type': Transaction.DEPOSIT,
            }
        form = DepositForm(data)
        self.assertTrue(form.is_valid())
        form.save()
        data['src'] = 'Job b'
        form = DepositForm(data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(len(Account.objects.filter(
            account_type=AccountType.FOREIGN)), 2)

    def test_different_expense_accounts(self):
        data = {
            'title': 'withdraw',
            'src': self.account.pk,
            'dst': 'Supermarket a',
            'amount': 123,
            'date': '2017-01-01'
            }
        form = WithdrawForm(data)
        self.assertTrue(form.is_valid())
        form.save()
        data['dst'] = 'Supermarket b'
        form = WithdrawForm(data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(len(Account.objects.filter(
            account_type=AccountType.FOREIGN)), 2)

    def test_transfer_to_same_account(self):
        data = {
            'title': 'transfer',
            'src': self.account.pk,
            'dst': self.account.pk,
            'amount': 123,
            'date': '2017-01-01',
            'transaction_type': Transaction.TRANSFER
            }
        form = TransferForm(data)
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 2)
        self.assertEqual(len(form.errors['src']), 1)
        self.assertEqual(len(form.errors['dst']), 1)

    def test_transfer_form_only_shows_personal_accounts(self):
        pass
