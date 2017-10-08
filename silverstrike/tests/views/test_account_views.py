from datetime import date
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from silverstrike.models import Account, Transaction
from silverstrike.tests import create_transaction


class AbstractAccountViewTests(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin', email='email@example.com', password='pass')
        self.client.login(username='admin', password='pass')
        self.account = Account.objects.create(name='first account', show_on_dashboard=True)
        self.personal = Account.objects.create(name='personal account')
        self.expense = Account.objects.create(
            name="expense account", account_type=Account.EXPENSE)
        self.revenue = Account.objects.create(
            name="revenue account", account_type=Account.REVENUE)


class AccountDetailViewTests(AbstractAccountViewTests):
    def test_no_month_in_url(self):
        context = self.client.get(reverse('account_view', args=[self.account.id])).context
        today = date.today()
        month = context['month']
        self.assertEquals(month.year, today.year)
        self.assertEquals(month.month, today.month)

    def test_view_system_account(self):
        system = Account.objects.get(account_type=Account.SYSTEM)
        response = self.client.get(reverse('account_view', args=[system.id]))
        self.assertEquals(response.status_code, 404)

    def test_correct_income(self):
        pass

    def test_correct_expenses(self):
        pass

    def test_correct_difference(self):
        pass

    def test_correct_balance(self):
        pass

    def test_next_month(self):
        pass

    def test_previous_month(self):
        pass

    def test_dataset_for_personal_accounts(self):
        pass

    def test_dataset_absence_for_expense_accounts(self):
        pass

    def test_dataset_absence_for_revenue_accounts(self):
        pass


class AccountCreateViewTests(AbstractAccountViewTests):
    def test_context_AccountCreate(self):
        context = self.client.get(reverse('account_new')).context
        self.assertEquals(context['menu'], 'accounts')


class AccountIndexViewTests(AbstractAccountViewTests):
    def test_context_with_no_transactions(self):
        context = self.client.get(reverse('accounts')).context
        self.assertEquals(context['menu'], 'accounts')
        self.assertEquals(len(context['accounts']), 2)
        self.assertEquals(context['accounts'][0]['id'], self.account.id)
        self.assertEquals(context['accounts'][0]['name'], self.account.name)
        self.assertEquals(context['accounts'][0]['active'], self.account.active)
        self.assertEquals(context['accounts'][0]['balance'], self.account.balance)

    def test_context_with_transaction(self):
        create_transaction('meh', self.personal, self.expense, 100, Transaction.WITHDRAW)
        context = self.client.get(reverse('accounts')).context
        self.assertEquals(context['menu'], 'accounts')
        self.assertEquals(len(context['accounts']), 2)
        self.assertEquals(context['accounts'][0]['id'], self.account.id)
        self.assertEquals(context['accounts'][0]['name'], self.account.name)
        self.assertEquals(context['accounts'][0]['active'], self.account.active)
        self.assertEquals(context['accounts'][0]['balance'], self.account.balance)


class AccountUpdateTests(AbstractAccountViewTests):
    def test_personal_AccountUpdateView(self):
        context = self.client.get(reverse('account_update', args=[self.account.id])).context
        self.assertIn('name', context['form'].fields)
        self.assertIn('show_on_dashboard', context['form'].fields)
        self.assertIn('active', context['form'].fields)

    def test_revenue_AccountUpdateView(self):
        context = self.client.get(reverse('account_update', args=[self.revenue.id])).context
        self.assertIn('name', context['form'].fields)
        self.assertNotIn('show_on_dashboard', context['form'].fields)
        self.assertNotIn('active', context['form'].fields)

    def test_expense_AccountUpdateView(self):
        context = self.client.get(reverse('account_update', args=[self.expense.id])).context
        self.assertIn('name', context['form'].fields)
        self.assertNotIn('show_on_dashboard', context['form'].fields)
        self.assertNotIn('active', context['form'].fields)

    def test_system_AccountUpdateView(self):
        system = Account.objects.get(account_type=Account.SYSTEM)
        response = self.client.get(reverse('account_update', args=[system.id]))
        self.assertEquals(response.status_code, 404)


class AccountDeleteTests(AbstractAccountViewTests):
    def test_delete_personal_account(self):
        response = self.client.get(reverse('account_delete', args=[self.account.id]))
        self.assertEquals(200, response.status_code)
        self.assertEquals(self.account, response.context['object'])

    def test_delete_system_account(self):
        system = Account.objects.get(account_type=Account.SYSTEM)
        response = self.client.get(reverse('account_delete', args=[system.id]))
        self.assertEquals(404, response.status_code)
