from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from silverstrike.models import Account, AccountType, Transaction
from silverstrike.models import TransactionAccountTypeValidationError, \
    TransactionSignValidationError
from silverstrike.tests import create_transaction


class TransactionQuerySetTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='personal')
        self.foreign = Account.objects.create(
            name='foreign',
            account_type=AccountType.FOREIGN)

    def test_last_10_returns_at_most_10(self):
        for i in range(1, 32):
            create_transaction('meh', self.foreign, self.personal, 50, Transaction.DEPOSIT,
                               date=date(2018, 1, i))
        queryset = Transaction.objects.last_10()
        self.assertEqual(queryset.count(), 10)
        # they have to be the last ones
        for t in queryset:
            self.assertGreater(t.date.day, 20)

    def test_last_10_returns_something(self):
        create_transaction('meh', self.foreign, self.personal, 50, Transaction.DEPOSIT,
                           date=date(2018, 1, 1))
        self.assertEqual(Transaction.objects.last_10().count(), 1)


class TransactionValidationTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='personal')
        self.savings = Account.objects.create(name='savings')
        self.foreign = Account.objects.create(
            name='foreign',
            account_type=AccountType.FOREIGN)

    def assert_account_type_error_message(self, error, account, transaction_type, account_slot):
        self.assertIn(
            TransactionAccountTypeValidationError(account.account_type_str, transaction_type, account_slot).message,
            error.exception.messages)

    def test_creating_transactions_deposit_source_requires_correct_account_types(self):
        wrong_account = self.personal
        with self.assertRaises(ValidationError,
                               msg="create deposit transaction with incorrect accounts results in errors") as error:
            create_transaction('meh', wrong_account, self.personal, 50, Transaction.DEPOSIT,
                               date=date(2018, 1, 1))
        self.assert_account_type_error_message(error, wrong_account, "Deposit", "source")

    def test_creating_transactions_deposit_destination_requires_correct_account_types(self):
        wrong_account = self.foreign
        with self.assertRaises(ValidationError,
                               msg="create deposit transaction with incorrect accounts results in errors") as error:
            create_transaction('meh', self.foreign, wrong_account, 50, Transaction.DEPOSIT,
                               date=date(2018, 1, 1))
        self.assert_account_type_error_message(error, wrong_account, "Deposit", "destination")

    def test_creating_transactions_withdraw_source_requires_correct_account_types(self):
        wrong_account = self.foreign
        with self.assertRaises(ValidationError,
                               msg="create withdraw transaction with incorrect accounts results in errors") as error:
            create_transaction('meh', wrong_account, self.foreign, 50, Transaction.WITHDRAW,
                               date=date(2018, 1, 1))
        self.assert_account_type_error_message(error, wrong_account, "Withdraw", "source")

    def test_creating_transactions_withdraw_destination_requires_correct_account_types(self):
        wrong_account = self.personal
        with self.assertRaises(ValidationError,
                               msg="create withdraw transaction with incorrect accounts results in errors") as error:
            create_transaction('meh', self.personal, wrong_account, 50, Transaction.WITHDRAW,
                               date=date(2018, 1, 1))
        self.assert_account_type_error_message(error, wrong_account, "Withdraw", "destination")

    def test_creating_transactions_transfer_source_requires_correct_account_types(self):
        wrong_account = self.foreign
        with self.assertRaises(ValidationError,
                               msg="create transfer transaction with incorrect accounts results in errors") as error:
            create_transaction('meh', wrong_account, self.personal, 50, Transaction.TRANSFER,
                               date=date(2018, 1, 1))
        self.assert_account_type_error_message(error, wrong_account, "Transfer", "source")

    def test_creating_transactions_transfer_destination_requires_correct_account_types(self):
        wrong_account = self.foreign
        with self.assertRaises(ValidationError,
                               msg="create withdraw transaction with incorrect accounts results in errors") as error:
            create_transaction('meh', self.personal, wrong_account, 50, Transaction.TRANSFER,
                               date=date(2018, 1, 1))
        self.assert_account_type_error_message(error, wrong_account, "Transfer", "destination")

    def test_creating_transactions_requires_positive_amounts_deposit(self):
        with self.assertRaises(ValidationError,
                               msg="create transaction with negative amounts results in errors") as error:
            create_transaction('meh', self.foreign, self.personal, -50, Transaction.DEPOSIT,
                               date=date(2018, 1, 1))
        self.assertIn(TransactionSignValidationError().message, error.exception.messages)

    def test_creating_transactions_requires_positive_amounts_withdraw(self):
        with self.assertRaises(ValidationError,
                               msg="create transaction with negative amounts results in errors") as error:
            create_transaction('meh', self.foreign, self.personal, -50, Transaction.WITHDRAW,
                               date=date(2018, 1, 1))
        self.assertIn(TransactionSignValidationError().message, error.exception.messages)

    def test_creating_transactions_requires_positive_amounts_transfer(self):
        with self.assertRaises(ValidationError,
                               msg="create transaction with negative amounts results in errors") as error:
            create_transaction('meh', self.foreign, self.personal, -50, Transaction.TRANSFER,
                               date=date(2018, 1, 1))
        self.assertIn(TransactionSignValidationError().message, error.exception.messages)


class TransactionModelTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='personal')
        self.savings = Account.objects.create(name='savings')
        self.foreign = Account.objects.create(
            name='foreign',
            account_type=AccountType.FOREIGN)

    def test_transaction_str_method(self):
        transaction = create_transaction('transaction', self.personal, self.foreign,
                                         10, Transaction.WITHDRAW)
        self.assertEqual(str(transaction), transaction.title)

    def test_absolute_url(self):
        transaction = create_transaction('transaction', self.personal, self.foreign,
                                         10, Transaction.WITHDRAW)
        self.assertEqual(transaction.get_absolute_url(),
                         reverse('transaction_detail', args=[transaction.pk]))

    def test_withdraw_amount(self):
        transaction = create_transaction('meh', self.personal, self.foreign,
                                         100, Transaction.WITHDRAW)
        self.assertEqual(transaction.amount, 100)

    def test_transfer_amount(self):
        transaction = create_transaction('meh', self.personal, self.savings,
                                         100, Transaction.TRANSFER)
        self.assertEqual(transaction.amount, 100)

    def test_deposit_amount(self):
        transaction = create_transaction('meh', self.foreign, self.personal,
                                         100, Transaction.DEPOSIT)
        self.assertEqual(transaction.amount, 100)

    def test_system_amount(self):
        self.personal.set_initial_balance(100)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.amount, 100)

    def test_transaction_type_string_withdraw(self):
        transaction = create_transaction('meh', self.personal, self.foreign,
                                         100, Transaction.WITHDRAW)
        self.assertEqual(transaction.get_transaction_type_str(), 'Withdrawal')

    def test_transaction_type_string_deposit(self):
        transaction = create_transaction('meh', self.foreign, self.personal,
                                         100, Transaction.DEPOSIT)
        self.assertEqual(transaction.get_transaction_type_str(), 'Deposit')

    def test_transaction_type_string_transfer(self):
        transaction = create_transaction('meh', self.personal, self.savings,
                                         100, Transaction.TRANSFER)
        self.assertEqual(transaction.get_transaction_type_str(), 'Transfer')

    def test_transaction_type_string_system(self):
        self.personal.set_initial_balance(100)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.get_transaction_type_str(), 'Reconcile')

    def test_is_transfer(self):
        transaction = create_transaction('meh', self.personal, self.savings,
                                         100, Transaction.TRANSFER)
        self.assertTrue(transaction.is_transfer)
        self.assertFalse(transaction.is_withdraw)
        self.assertFalse(transaction.is_deposit)
        self.assertFalse(transaction.is_system)

    def test_is_withdraw(self):
        transaction = create_transaction('meh', self.personal, self.foreign,
                                         100, Transaction.WITHDRAW)
        self.assertFalse(transaction.is_transfer)
        self.assertTrue(transaction.is_withdraw)
        self.assertFalse(transaction.is_deposit)
        self.assertFalse(transaction.is_system)

    def test_is_deposit(self):
        transaction = create_transaction('meh', self.foreign, self.personal,
                                         100, Transaction.DEPOSIT)
        self.assertFalse(transaction.is_transfer)
        self.assertFalse(transaction.is_withdraw)
        self.assertTrue(transaction.is_deposit)
        self.assertFalse(transaction.is_system)

    def test_is_system(self):
        self.personal.set_initial_balance(100)
        transaction = Transaction.objects.first()
        self.assertFalse(transaction.is_transfer)
        self.assertFalse(transaction.is_withdraw)
        self.assertFalse(transaction.is_deposit)
        self.assertTrue(transaction.is_system)
