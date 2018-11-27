from datetime import date

from silverstrike.models import (Account, RecurringSplit, RecurringTransaction,
                                 Split, Transaction)


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


def create_recurring_transaction(title, src, dst, amount, type, recurrence,
                                 skip=0, date=date.today(), last_day_in_month=False):
    r = RecurringTransaction.objects.create(
        title=title, date=date, transaction_type=type, recurrence=recurrence, skip=skip,
        last_day_in_month=last_day_in_month)
    RecurringSplit.objects.bulk_create([
        RecurringSplit(title=title, account=src, opposing_account=dst,
                       amount=-amount, transaction=r, date=date),
        RecurringSplit(title=title, account=dst, opposing_account=src,
                       amount=amount, transaction=r, date=date)])
    return r
