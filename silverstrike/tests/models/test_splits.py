from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from silverstrike.models import (Account, AccountType, Category,
                                 RecurringTransaction, Split, Transaction)
from silverstrike.models import TransactionSplitConsistencyValidationError, \
    TransactionSplitSumValidationError
from silverstrike.tests import create_transaction, create_transaction_with_splits


class SplitQuerySetTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='personal')
        self.savings = Account.objects.create(name='savings')
        self.foreign = Account.objects.create(
            name='foreign',
            account_type=AccountType.FOREIGN)

        self.transfer_transaction = create_transaction(
            'transfer', self.personal, self.savings, 100, Transaction.TRANSFER, date(2017, 1, 1))
        self.deposit_transaction = create_transaction(
            'deposit', self.foreign, self.personal, 100, Transaction.DEPOSIT, date(2017, 6, 1))
        self.withdraw_transaction = create_transaction(
            'withdraw', self.personal, self.foreign, 100, Transaction.WITHDRAW, date(2017, 12, 1))
        self.upcoming_transaction = create_transaction(
            'upcoming', self.personal, self.foreign, 100, Transaction.WITHDRAW, date(2200, 1, 1))

    def test_personal(self):
        queryset = Split.objects.personal()
        # we should get exactly 5 results. One for each, plus an additional for a transfer
        self.assertEqual(queryset.count(), 5)

    def test_transfers_once(self):
        queryset = Split.objects.personal().transfers_once()
        # this time we should get exactly 4.
        self.assertEqual(queryset.count(), 4)

    def test_exclude_transfers(self):
        queryset = Split.objects.personal().exclude_transfers()
        # this time we get 3. the transfer is not included
        self.assertEqual(queryset.count(), 3)

    def test_income(self):
        queryset = Split.objects.personal().income()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.deposit_transaction)

    def test_expense(self):
        queryset = Split.objects.personal().expense()
        self.assertEqual(queryset.count(), 2)
        queryset = queryset.past()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.withdraw_transaction)

    def test_date_range_includes_start(self):
        queryset = Split.objects.personal().date_range(date(2017, 6, 1), date(2017, 7, 1))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.deposit_transaction)

    def test_date_range_includes_end(self):
        queryset = Split.objects.personal().date_range(date(2017, 5, 1), date(2017, 6, 1))
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.deposit_transaction)

    def test_category(self):
        category = Category.objects.create(name='category')
        for s in self.withdraw_transaction.splits.all():
            s.category = category
            s.save()
        queryset = Split.objects.personal().category(category)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.withdraw_transaction)

    def test_upcoming(self):
        queryset = Split.objects.personal().upcoming()
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.upcoming_transaction)

    def test_past(self):
        queryset = Split.objects.personal().exclude_transfers().past()
        self.assertEqual(queryset.count(), 2)

    def test_recurrence(self):
        recurrence = RecurringTransaction.objects.create(
            title='some recurrence',
            amount=25,
            date=date.today(),
            src=self.personal,
            dst=self.foreign,
            interval=RecurringTransaction.MONTHLY,
            transaction_type=Transaction.WITHDRAW)
        self.withdraw_transaction.recurrence = recurrence
        self.withdraw_transaction.save()
        queryset = Split.objects.personal().recurrence(recurrence)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset.first().transaction, self.withdraw_transaction)


class SplitModelTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='personal')
        self.savings = Account.objects.create(name='savings')
        self.foreign = Account.objects.create(
            name='foreign',
            account_type=AccountType.FOREIGN)

    def test_split_str_method(self):
        transaction = create_transaction('meh',
                                         src=self.foreign,
                                         dst=self.personal,
                                         amount=100,
                                         type=Transaction.DEPOSIT)
        split = transaction.splits.first()
        self.assertEqual(str(split), split.title)

    def test_split_absolute_url(self):
        account = Account.objects.create(name="foo")
        account.set_initial_balance(10)
        split = Split.objects.first()
        self.assertEqual(split.get_absolute_url(), reverse('transaction_detail',
                                                           args=[split.transaction.id]))


class SplitValidationTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='personal')
        self.savings = Account.objects.create(name='savings')
        self.foreign = Account.objects.create(
            name='foreign',
            account_type=AccountType.FOREIGN)

    def test_split_raises_validation_error_for_unbalanced_sum(self):
        unbalanced_split = [
            Split(title="meh split 1",
                  account=self.personal,
                  opposing_account=self.foreign,
                  amount=-50,
                  date=date.today()),
            Split(title="meh split 2",
                  account=self.foreign,
                  opposing_account=self.personal,
                  amount=70,
                  date=date.today())
        ]

        with self.assertRaises(ValidationError,
                               msg="create transaction with splits should validate "
                                   "transaction is in balance") as error:
            create_transaction_with_splits('meh',
                                           self.personal,
                                           self.foreign,
                                           70,
                                           Transaction.WITHDRAW,
                                           unbalanced_split)
        self.assert_split_sum_error(error, self.personal)

    def test_split_validates_amount_sum(self):
        balanced_split = [
            Split(title="meh split 1", account=self.personal, opposing_account=self.foreign,
                  amount=-50, date=date.today()),
            Split(title="meh split 2", account=self.foreign, opposing_account=self.personal,
                  amount=25, date=date.today()),
            Split(title="meh split 3", account=self.foreign, opposing_account=self.personal,
                  amount=25, date=date.today()),
        ]

        create_transaction_with_splits('meh', self.personal, self.foreign, 50,
                                       Transaction.WITHDRAW,
                                       balanced_split)

    def test_transaction_validates_split_sum_is_correct_sign_withdraw(self):
        balanced_split = [
            Split(title="meh split 1", account=self.personal, opposing_account=self.foreign,
                  amount=50, date=date.today()),
            Split(title="meh split 1", account=self.foreign, opposing_account=self.personal,
                  amount=-50, date=date.today()),
        ]

        with self.assertRaises(ValidationError,
                               msg="create transaction with splits should validate "
                                   "transaction consistent with split") as error:
            create_transaction_with_splits('meh', self.personal, self.foreign, 50,
                                           Transaction.WITHDRAW,
                                           balanced_split)
        self.assertIn(TransactionSplitConsistencyValidationError(
            self.personal, "-50.00", 50).message, error.exception.messages)

    def test_transaction_validates_split_sum_is_correct_sign_deposit(self):
        balanced_split = [
            Split(title="meh split 1", account=self.personal, opposing_account=self.foreign,
                  amount=-50, date=date.today()),
            Split(title="meh split 2", account=self.foreign, opposing_account=self.personal,
                  amount=50, date=date.today()),
        ]

        with self.assertRaises(ValidationError,
                               msg="create transaction with splits should validate "
                                   "transaction consistent with split") as error:
            create_transaction_with_splits('meh',
                                           src=self.foreign,
                                           dst=self.personal,
                                           amount=50,
                                           type=Transaction.DEPOSIT,
                                           splits=balanced_split)
        self.assertIn(TransactionSplitConsistencyValidationError(
            self.foreign, "-50.00", 50).message, error.exception.messages)

    def test_transaction_validates_split_sum_is_correct_sign_transfer(self):
        balanced_split = [
            Split(title="meh split 1", account=self.personal, opposing_account=self.savings,
                  amount=-50, date=date.today()),
            Split(title="meh split 2", account=self.savings, opposing_account=self.personal,
                  amount=50, date=date.today()),
        ]

        with self.assertRaises(ValidationError,
                               msg="create transaction with splits should validate "
                                   "transaction consistent with split") as error:
            create_transaction_with_splits('meh',
                                           src=self.savings,
                                           dst=self.personal,
                                           amount=50,
                                           type=Transaction.TRANSFER,
                                           splits=balanced_split)
        self.assertIn(TransactionSplitConsistencyValidationError(
            self.savings, "-50.00", 50).message, error.exception.messages)

    def test_transaction_validates_split_sum_is_transaction_amount(self):
        balanced_split = [
            Split(title="meh split 1", account=self.personal, opposing_account=self.foreign,
                  amount=-50, date=date.today()),
            Split(title="meh split 2", account=self.foreign, opposing_account=self.personal,
                  amount=25, date=date.today()),
            Split(title="meh split 3", account=self.foreign, opposing_account=self.personal,
                  amount=25, date=date.today()),
        ]

        with self.assertRaises(ValidationError,
                               msg="create transaction with splits should validate "
                                   "transaction consistent with split") as error:
            create_transaction_with_splits('meh', self.personal, self.foreign, 70,
                                           Transaction.WITHDRAW,
                                           balanced_split)
        self.assertIn(TransactionSplitConsistencyValidationError(
            self.personal, "50.00", 70).message, error.exception.messages)

    def assert_split_sum_error(self, error, account):
        self.assertIn(TransactionSplitSumValidationError(account).message, error.exception.messages)
