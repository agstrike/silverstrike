from django.test import TestCase

from silverstrike.forms import RecurringTransactionForm
from silverstrike.models import Account, Transaction


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
            'amount': -100, 'transaction_type': Transaction.TRANSFER,
            'src': personal, 'dst': other})
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)
