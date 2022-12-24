from django.core.exceptions import ValidationError


class TransactionSignValidationError(ValidationError):
    def __init__(self):
        super().__init__(f"Transaction amounts must be positive.")


class TransactionAccountTypeValidationError(ValidationError):
    def __init__(self, account_type, transaction_type, account_slot):
        super().__init__(
            f"Transaction account type {account_type} is not allowed in "
            f"{transaction_type} transaction {account_slot}")


class TransactionSplitSumValidationError(ValidationError):
    def __init__(self, account):
        super().__init__(f"Can't validate splits for account:{account} are in balance")


class TransactionSplitConsistencyValidationError(ValidationError):
    def __init__(self, account, account_amount, transaction_amount):
        super().__init__(
            f"Can't validate splits for account:{account} (${account_amount}) "
            f"equal transaction amount (${transaction_amount})")
