from django.test import TestCase

from silverstrike.forms import ReconcilationForm
from silverstrike.models import Account, Transaction


class ReconcilationFormTests(TestCase):
    def setUp(self):
        self.account = Account.objects.create(name='personal')
        self.account.set_initial_balance(100)

    def test_same_balance(self):
        form = ReconcilationForm({'balance': '100', 'title': 'meh'}, account=self.account.id)
        self.assertFalse(form.is_valid())

    def test_increasing_balance(self):
        form = ReconcilationForm({'balance': '150', 'title': 'meh'}, account=self.account.id)
        self.assertTrue(form.is_valid())
        self.assertEqual(self.account.balance, 100)
        form.save()
        self.assertEqual(self.account.balance, 150)
        self.assertEqual(Transaction.objects.last().amount, 50)
        self.assertEqual(Transaction.objects.last().transaction_type, Transaction.SYSTEM)

    def test_decreasing_balance(self):
        form = ReconcilationForm({'balance': '50', 'title': 'meh'}, account=self.account.id)
        self.assertTrue(form.is_valid())
        self.assertEqual(self.account.balance, 100)
        form.save()
        self.assertEqual(self.account.balance, 50)
        self.assertEqual(Transaction.objects.last().amount, 50)
        self.assertEqual(Transaction.objects.last().transaction_type, Transaction.SYSTEM)
