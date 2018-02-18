from datetime import date

from silverstrike.models import Account, Split, Transaction


def create_transaction(title, src, dst, amount, type, date=date.today()):
    t = Transaction.objects.create(title=title, date=date, transaction_type=type)
    Split.objects.bulk_create([
        Split(title=title, account=src, opposing_account=dst,
              amount=-amount, transaction=t, date=date),
        Split(title=title, account=dst, opposing_account=src,
              amount=amount, transaction=t, date=date)])
    return t


def create_account(name, account_type=Account.PERSONAL):
    return Account.objects.create(name=name, account_type=account_type)
