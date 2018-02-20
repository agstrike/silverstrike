import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from silverstrike import forms
from silverstrike.models import Account, Transaction
from silverstrike.tests import create_transaction


class AbstractAccountViewTests(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin', email='email@example.com', password='pass')
        self.client.login(username='admin', password='pass')
        self.account = Account.objects.create(name='first account', show_on_dashboard=True)
        self.personal = Account.objects.create(name='personal account')
        self.expense = Account.objects.create(
            name="expense account", account_type=Account.FOREIGN)
        self.revenue = Account.objects.create(
            name="revenue account", account_type=Account.FOREIGN)


class AccountDetailViewTests(AbstractAccountViewTests):
    def test_no_daterange_in_url(self):
        context = self.client.get(reverse('account_view', args=[self.account.id])).context
        today = datetime.date.today()
        self.assertEqual(context['dend'], today)
        self.assertEqual(context['dstart'], today - datetime.timedelta(days=30))

    def test_view_system_account(self):
        system = Account.objects.get(account_type=Account.SYSTEM)
        response = self.client.get(reverse('account_view', args=[system.id]))
        self.assertEqual(response.status_code, 403)

    def test_correct_income(self):
        create_transaction('meh', self.revenue, self.account, 100, Transaction.DEPOSIT)
        context = self.client.get(reverse('account_view', args=[self.account.id])).context
        self.assertEqual(context['out'], 0)
        self.assertEqual(context['in'], 100)
        self.assertEqual(context['difference'], 100)
        self.assertEqual(context['balance'], 100)

    def test_correct_expenses(self):
        create_transaction('meh', self.account, self.expense, 100, Transaction.WITHDRAW)
        context = self.client.get(reverse('account_view', args=[self.account.id])).context
        self.assertEqual(context['out'], -100)
        self.assertEqual(context['in'], 0)
        self.assertEqual(context['difference'], -100)
        self.assertEqual(context['balance'], -100)

    def test_correct_difference(self):
        create_transaction('meh', self.revenue, self.account, 100, Transaction.DEPOSIT)
        create_transaction('meh', self.account, self.expense, 50, Transaction.WITHDRAW)
        context = self.client.get(reverse('account_view', args=[self.account.id])).context
        self.assertEqual(context['out'], -50)
        self.assertEqual(context['in'], 100)
        self.assertEqual(context['difference'], 50)
        self.assertEqual(context['balance'], 50)

    def test_display_all_transactions(self):
        create_transaction('meh', self.revenue, self.account, 500, Transaction.DEPOSIT,
                           date=datetime.date(2017, 1, 1))
        create_transaction('meh', self.account, self.expense, 100, Transaction.WITHDRAW,
                           date=datetime.date(2018, 1, 1))
        context = self.client.get(reverse('account_detail_all', args=[self.account.id])).context
        self.assertEqual(context['dstart'], datetime.date(2017, 1, 1))
        self.assertEqual(context['dend'], datetime.date(2018, 1, 1))
        self.assertEqual(context['out'], -100)
        self.assertEqual(context['in'], 500)
        self.assertEqual(context['difference'], 400)
        self.assertEqual(context['balance'], 400)

    def test_display_custom_range(self):
        create_transaction('meh', self.revenue, self.account, 500, Transaction.DEPOSIT,
                           date=datetime.date(2017, 1, 1))
        create_transaction('meh', self.account, self.expense, 100, Transaction.WITHDRAW,
                           date=datetime.date(2018, 1, 1))
        context = self.client.get(reverse('account_detail', args=[
            self.account.id, datetime.date(2017, 6, 1), datetime.date(2018, 2, 1)])).context
        self.assertEqual(context['dstart'], datetime.date(2017, 6, 1))
        self.assertEqual(context['dend'], datetime.date(2018, 2, 1))
        self.assertEqual(context['out'], -100)
        self.assertEqual(context['in'], 0)
        self.assertEqual(context['difference'], -100)
        self.assertEqual(context['balance'], 400)

    def test_invalid_custom_range_results_in_404(self):
        response = self.client.get(reverse('account_detail', args=[
            self.account.id, 'asdf', datetime.date(2018, 2, 1)]))
        self.assertEqual(response.status_code, 400)

    def test_future_transaction_does_not_affect_calculations(self):
        create_transaction('meh', self.revenue, self.account, 500, Transaction.DEPOSIT,
                           date=datetime.date(2017, 1, 1))
        create_transaction('meh', self.account, self.expense, 100, Transaction.WITHDRAW,
                           date=datetime.date(2018, 1, 1))
        create_transaction('meh', self.account, self.expense, 50, Transaction.WITHDRAW,
                           date=datetime.date(2200, 1, 1))
        context = self.client.get(reverse('account_detail_all', args=[self.account.id])).context
        self.assertEqual(context['dstart'], datetime.date(2017, 1, 1))
        self.assertEqual(context['dend'], datetime.date(2200, 1, 1))
        self.assertEqual(context['out'], -100)
        self.assertEqual(context['in'], 500)
        self.assertEqual(context['difference'], 400)
        self.assertEqual(context['balance'], 400)

    def test_account_with_no_transactions(self):
        response = self.client.get(reverse('account_view', args=[self.account.id]))
        self.assertEqual(response.status_code, 200)

    def test_account_with_no_transaction_view_all(self):
        response = self.client.get(reverse('account_detail_all', args=[self.account.id]))
        self.assertEqual(response.status_code, 200)

    def test_account_with_no_transaction_custom_range(self):
        response = self.client.get(reverse('account_detail', args=[
            self.account.id, datetime.date(2017, 6, 1), datetime.date(2018, 2, 1)]))
        self.assertEqual(response.status_code, 200)

    def test_dataset_for_personal_accounts(self):
        """
        TODO Not sure how to test that...
        """
        pass


class AccountCreateViewTests(AbstractAccountViewTests):
    def test_context_AccountCreate(self):
        context = self.client.get(reverse('account_new')).context
        self.assertEqual(context['menu'], 'accounts')
        self.assertIsInstance(context['form'], forms.AccountCreateForm)

    def test_post_valid(self):
        pass

    def test_post_invalid(self):
        pass


class AccountIndexViewTests(AbstractAccountViewTests):
    def test_context_with_no_transactions(self):
        context = self.client.get(reverse('accounts')).context
        self.assertEqual(context['menu'], 'accounts')
        self.assertEqual(len(context['accounts']), 2)
        self.assertEqual(context['accounts'][0]['id'], self.account.id)
        self.assertEqual(context['accounts'][0]['name'], self.account.name)
        self.assertEqual(context['accounts'][0]['active'], self.account.active)
        self.assertEqual(context['accounts'][0]['balance'], self.account.balance)

    def test_context_with_transaction(self):
        create_transaction('meh', self.personal, self.expense, 100, Transaction.WITHDRAW)
        context = self.client.get(reverse('accounts')).context
        self.assertEqual(context['menu'], 'accounts')
        self.assertEqual(len(context['accounts']), 2)
        self.assertEqual(context['accounts'][0]['id'], self.account.id)
        self.assertEqual(context['accounts'][0]['name'], self.account.name)
        self.assertEqual(context['accounts'][0]['active'], self.account.active)
        self.assertEqual(context['accounts'][0]['balance'], self.account.balance)


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
        self.assertEqual(response.status_code, 403)


class AccountDeleteTests(AbstractAccountViewTests):
    def test_delete_personal_account(self):
        response = self.client.get(reverse('account_delete', args=[self.account.id]))
        self.assertEqual(200, response.status_code)
        self.assertEqual(self.account, response.context['object'])

    def test_delete_system_account(self):
        system = Account.objects.get(account_type=Account.SYSTEM)
        response = self.client.get(reverse('account_delete', args=[system.id]))
        self.assertEqual(response.status_code, 403)


class AccountReconcileView(AbstractAccountViewTests):
    def test_personal_account(self):
        response = self.client.get(reverse('account_reconcile', args=[self.account.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], forms.ReconcilationForm)
        self.assertEqual(response.context['account'], self.account)

    def test_revenue_account(self):
        response = self.client.get(reverse('account_reconcile', args=[self.revenue.id]))
        self.assertEqual(response.status_code, 403)

    def test_expense_account(self):
        response = self.client.get(reverse('account_reconcile', args=[self.expense.id]))
        self.assertEqual(response.status_code, 403)

    def test_system_account(self):
        system = Account.objects.get(account_type=Account.SYSTEM)
        response = self.client.get(reverse('account_reconcile', args=[system.id]))
        self.assertEqual(response.status_code, 403)

    def test_post_valid(self):
        pass

    def test_post_invalid(self):
        pass
