from django.test import TestCase

from pyaccountant.forms import DepositForm, TransferForm, WithdrawForm
from pyaccountant.models import Account, InternalAccountType, TransactionJournal


class FormTests(TestCase):
    def setUp(self):
        self.account = Account.objects.create(
            name="first account", internal_type=InternalAccountType.personal.value)
        self.personal = Account.objects.create(
            name="personal account", internal_type=InternalAccountType.personal.value)

    def test_TransferForm(self):
        data = {
            'title': 'transfer',
            'source_account': 1,
            'destination_account': 2,
            'amount': 123,
            'date': '2017-01-01'
            }
        form = TransferForm(data)
        self.assertTrue(form.is_valid())
        transfer = form.save()
        self.assertIsInstance(transfer, TransactionJournal)

    def test_DepositForm(self):
        data = {
            'title': 'transfer',
            'source_account': 'Work account',
            'destination_account': 2,
            'amount': 123,
            'date': '2017-01-01'
            }
        form = DepositForm(data)
        self.assertTrue(form.is_valid())
        transfer = form.save()
        self.assertIsInstance(transfer, TransactionJournal)

    def test_WithdrawForm(self):
        data = {
            'title': 'transfer',
            'source_account': 1,
            'destination_account': 'Supermarket a',
            'amount': 123,
            'date': '2017-01-01'
            }
        form = WithdrawForm(data)
        self.assertTrue(form.is_valid())
        transfer = form.save()
        self.assertIsInstance(transfer, TransactionJournal)
