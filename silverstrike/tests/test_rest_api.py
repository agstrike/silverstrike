import copy
from datetime import date

from django.test import TestCase
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as RestValidationError

from silverstrike.models import Account, AccountType, Transaction
from silverstrike.models.errors import TransactionSplitSumValidationError
from silverstrike.rest.serializers import TransactionSerializer


def create_split(title, src, dst, amount, date=date.today(), category=None):
    return {"title": title,
            "account": src,
            "opposing_account": dst,
            "amount": amount,
            "date": date.today(),
            "category": category
            }


def create_rest_transaction_with_splits(title, src, dst, amount, type, splits, date=date.today()):
    serializer = TransactionSerializer()
    data = {
        "title": title,
        "src": src,
        "dst": dst,
        "amount": amount,
        "transaction_type": type,
        "date": date,
        "splits": splits
    }
    validated = serializer.validate(data)
    return serializer.create(validated)


class RestTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='personal')
        self.foreign = Account.objects.create(
            name='foreign',
            account_type=AccountType.FOREIGN)

    def test_rest_validates_required_fields_are_set(self):
        serializer = TransactionSerializer()

        all_data = {
            "title": 'meh',
            "src": self.personal,
            "dst": self.foreign,
            "amount": 44.44,
            "transaction_type": 2,
            "date": date.today(),
        }
        for f in all_data.keys():
            data = copy.copy(all_data)
            data.pop(f)
            with self.assertRaises(RestValidationError):
                serializer.validate(data)

    def test_split_raises_validation_error_for_unbalanced_sum(self):
        unbalanced_split = [create_split("meh split 1",
                                         self.personal,
                                         self.foreign,
                                         -50),
                            create_split("meh split 2",
                                         self.foreign,
                                         self.personal,
                                         70)]

        with self.assertRaises(DjangoValidationError,
                               msg="create transaction with splits should validate "
                                   "transaction is in balance") as error:
            create_rest_transaction_with_splits('meh',
                                                src=self.personal,
                                                dst=self.foreign,
                                                amount=70,
                                                type=Transaction.WITHDRAW,
                                                splits=unbalanced_split)
        self.assertIn(TransactionSplitSumValidationError(self.personal).message,
                      error.exception.messages)
