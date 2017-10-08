import datetime
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from silverstrike import forms
from silverstrike.lib import last_day_of_month
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
        today = datetime.date.today()
        month = context['month']
        self.assertEquals(month.year, today.year)
        self.assertEquals(month.month, today.month)

    def test_view_system_account(self):
        system = Account.objects.get(account_type=Account.SYSTEM)
        response = self.client.get(reverse('account_view', args=[system.id]))
        self.assertEquals(response.status_code, 404)

    def test_correct_income(self):
        create_transaction('meh', self.revenue, self.account, 100, Transaction.DEPOSIT)
        context = self.client.get(reverse('account_view', args=[self.account.id])).context
        self.assertEquals(context['expenses'], 0)
        self.assertEquals(context['income'], 100)
        self.assertEquals(context['difference'], 100)
        self.assertEquals(context['balance'], 100)

    def test_correct_expenses(self):
        create_transaction('meh', self.account, self.expense, 100, Transaction.WITHDRAW)
        context = self.client.get(reverse('account_view', args=[self.account.id])).context
        self.assertEquals(context['expenses'], -100)
        self.assertEquals(context['income'], 0)
        self.assertEquals(context['difference'], -100)
        self.assertEquals(context['balance'], -100)

    def test_correct_difference(self):
        create_transaction('meh', self.revenue, self.account, 100, Transaction.DEPOSIT)
        create_transaction('meh', self.account, self.expense, 50, Transaction.WITHDRAW)
        context = self.client.get(reverse('account_view', args=[self.account.id])).context
        self.assertEquals(context['expenses'], -50)
        self.assertEquals(context['income'], 100)
        self.assertEquals(context['difference'], 50)
        self.assertEquals(context['balance'], 50)

    def test_next_month(self):
        context = self.client.get(reverse('account_view', args=[self.account.id])).context
        next_month = last_day_of_month(datetime.date.today()) + datetime.timedelta(days=1)
        self.assertEquals(context['next_month'].month, next_month.month)
        self.assertEquals(context['next_month'].year, next_month.year)

    def test_previous_month(self):
        context = self.client.get(reverse('account_view', args=[self.account.id])).context
        previous_month = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
        self.assertEquals(context['previous_month'].month, previous_month.month)
        self.assertEquals(context['previous_month'].year, previous_month.year)

    def test_dataset_for_personal_accounts(self):
        """
        TODO Not sure how to test that...
        """
        pass

    def test_dataset_absence_for_expense_accounts(self):
        create_transaction('meh', self.revenue, self.account, 100, Transaction.DEPOSIT)
        create_transaction('meh', self.account, self.expense, 50, Transaction.WITHDRAW)
        context = self.client.get(reverse('account_view', args=[self.expense.id])).context
        self.assertFalse('dataset' in context)

    def test_dataset_absence_for_revenue_accounts(self):
        create_transaction('meh', self.revenue, self.account, 100, Transaction.DEPOSIT)
        create_transaction('meh', self.account, self.expense, 50, Transaction.WITHDRAW)
        context = self.client.get(reverse('account_view', args=[self.revenue.id])).context
        self.assertFalse('dataset' in context)


class AccountCreateViewTests(AbstractAccountViewTests):
    def test_context_AccountCreate(self):
        context = self.client.get(reverse('account_new')).context
        self.assertEquals(context['menu'], 'accounts')
        self.assertIsInstance(context['form'], forms.AccountCreateForm)

    def test_post_valid(self):
        pass

    def test_post_invalid(self):
        pass


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


class AccountReconcileView(AbstractAccountViewTests):
    def test_personal_account(self):
        response = self.client.get(reverse('account_reconcile', args=[self.account.id]))
        self.assertEquals(response.status_code, 200)
        self.assertIsInstance(response.context['form'], forms.ReconcilationForm)
        self.assertEquals(response.context['account'], self.account)

    def test_revenue_account(self):
        response = self.client.get(reverse('account_reconcile', args=[self.revenue.id]))
        self.assertEquals(response.status_code, 404)

    def test_expense_account(self):
        response = self.client.get(reverse('account_reconcile', args=[self.expense.id]))
        self.assertEquals(response.status_code, 404)

    def test_system_account(self):
        system = Account.objects.get(account_type=Account.SYSTEM)
        response = self.client.get(reverse('account_reconcile', args=[system.id]))
        self.assertEquals(response.status_code, 404)

    def test_post_valid(self):
        pass

    def test_post_invalid(self):
        pass
