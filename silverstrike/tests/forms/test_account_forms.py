from django.test import TestCase

from silverstrike import forms, models


class AccountCreateFormTests(TestCase):
    def test_available_fields(self):
        form = forms.AccountCreateForm()
        fields = ['name', 'initial_balance', 'active', 'show_on_dashboard']
        self.assertEqual(len(form.fields), len(fields))
        for field in fields:
            self.assertIn(field, form.fields)

    def test_form_saves_initial_balance(self):
        form = forms.AccountCreateForm({
            'name': 'foo', 'initial_balance': 100, 'active': True, 'show_on_dashboard': False})
        account = form.save()
        self.assertEqual(account.balance, 100)
        self.assertEqual(account.name, 'foo')
        self.assertTrue(account.active)
        self.assertFalse(account.show_on_dashboard)

    def test_unique_name(self):
        models.Account.objects.create(name='foo')
        form = forms.AccountCreateForm({
            'name': 'foo', 'initial_balance': 100, 'active': True
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertIn('name', form.errors)

    def test_unique_name_foregin_accounts(self):
        models.Account.objects.create(name='foo', account_type=models.AccountType.FOREIGN)
        form = forms.ForeignAccountForm({
            'name': 'foo'
        })
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertIn('name', form.errors)

    def test_unique_allows_different_types(self):
        models.Account.objects.create(name='foo', account_type=models.AccountType.FOREIGN)
        models.Account.objects.create(name='bar')
        form = forms.AccountCreateForm({
            'name': 'foo', 'initial_balance': 100, 'active': True
        })
        self.assertTrue(form.is_valid())

        form = forms.ForeignAccountForm({
            'name': 'bar'
        })
        self.assertTrue(form.is_valid())
