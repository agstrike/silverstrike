from datetime import date

from django.contrib.admin.sites import AdminSite
from django.test import TestCase

from silverstrike.admin import AccountAdmin
from silverstrike.models import Account, AccountType, RecurringTransaction, Split, Transaction
from silverstrike.tests import create_account, create_transaction


class MockRequest:
    pass


class MockSuperUser:
    def has_perm(self, perm):
        return True


class MockedAdmin(AccountAdmin):
    messages = []

    def message_user(self, request, message, message_type=None, **kwargs):
        self.messages.append(message)


request = MockRequest()
request.user = MockSuperUser()


class AccountAdminTests(TestCase):
    def setUp(self):
        self.first = create_account(name='first', account_type=AccountType.FOREIGN)
        self.second = create_account(name='second', account_type=AccountType.FOREIGN)
        self.third = create_account(name='third', account_type=AccountType.FOREIGN)
        self.personal = create_account(name='personal')
        create_transaction('first', self.personal, self.first, 50, Transaction.WITHDRAW)
        create_transaction('second', self.personal, self.second, 100, Transaction.WITHDRAW)
        create_transaction('second', self.personal, self.third, 25, Transaction.WITHDRAW)
        self.site = AdminSite()
        self.modeladmin = MockedAdmin(Account, self.site)

    def tearDown(self):
        self.modeladmin.messages.clear()

    def test_merge_three_foreign_accounts_produces_success(self):
        self.modeladmin.merge_accounts(request, Account.objects.foreign())
        self.assertEqual(len(self.modeladmin.messages), 1)
        self.assertIn('2 accounts', self.modeladmin.messages[0])

    def test_merge_two_foreign_accounts_produces_success(self):
        self.modeladmin.merge_accounts(request, Account.objects.foreign().exclude(pk=self.third.pk))
        self.assertEqual(len(self.modeladmin.messages), 1)
        self.assertIn('one account', self.modeladmin.messages[0])

    def test_merge_accounts_updates_splits(self):
        self.assertEqual(Split.objects.filter(account=self.second).count(), 1)
        self.assertEqual(Split.objects.filter(opposing_account=self.second).count(), 1)
        self.assertEqual(self.first.balance, 50)
        self.assertEqual(self.second.balance, 100)
        self.modeladmin.merge_accounts(request, Account.objects.foreign().exclude(pk=self.third.pk))
        self.assertEqual(Split.objects.filter(account=self.second).count(), 2)
        self.assertEqual(Split.objects.filter(opposing_account=self.second).count(), 2)
        self.assertEqual(self.second.balance, 150)

    def test_merge_accounts_results_in_correct_balances(self):
        self.assertEqual(self.first.balance, 50)
        self.assertEqual(self.second.balance, 100)
        self.modeladmin.merge_accounts(request, Account.objects.foreign().exclude(pk=self.third.pk))
        self.assertEqual(self.second.balance, 150)

    def test_merge_accounts_removes_accounts(self):
        self.assertEqual(Account.objects.foreign().count(), 3)
        self.modeladmin.merge_accounts(request, Account.objects.foreign().exclude(pk=self.third.pk))
        self.assertEqual(Account.objects.foreign().count(), 2)
        self.assertFalse(Account.objects.filter(pk=self.first.id).exists())

    def test_selecting_only_one_account(self):
        self.modeladmin.merge_accounts(request, Account.objects.filter(pk=self.third.pk))
        self.assertEqual(Account.objects.foreign().count(), 3)
        self.assertEqual(len(self.modeladmin.messages), 1)
        self.assertEqual('You need to select more than one account to merge them.',
                         self.modeladmin.messages[0])

    def test_merging_personal_accounts(self):
        create_account('second personal account')
        self.modeladmin.merge_accounts(request, Account.objects.personal())
        self.assertEqual(Account.objects.personal().count(), 2)
        self.assertEqual(len(self.modeladmin.messages), 2)
        self.assertIn('You can only merge foreign accounts, "personal" isn\'t.',
                      self.modeladmin.messages)
        self.assertIn('You can only merge foreign accounts, "second personal account" isn\'t.',
                      self.modeladmin.messages)

    def test_merging_account_updates_recurrence(self):
        recurrence = RecurringTransaction.objects.create(
            title='recurrence',
            amount=50,
            date=date.today(),
            src=self.personal,
            dst=self.first,
            interval=RecurringTransaction.MONTHLY,
            transaction_type=Transaction.WITHDRAW)
        self.modeladmin.merge_accounts(request, Account.objects.foreign().exclude(pk=self.third.pk))
        recurrence.refresh_from_db()
        self.assertEqual(recurrence.dst, self.second)
