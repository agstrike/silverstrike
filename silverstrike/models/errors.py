from django.core.exceptions import ValidationError


class TransactionSplitSumValidationError(ValidationError):
    def __init__(self, account):
        super().__init__(f"Can't validate splits for account:{account} are in balance")


class TransactionSplitConsistencyValidationError(ValidationError):
    def __init__(self, account):
        super().__init__(f"Can't validate splits for account:{account} equal transaction amount")

