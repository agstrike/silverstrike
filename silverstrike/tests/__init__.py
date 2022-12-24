from datetime import date

from silverstrike.models import Account, AccountType, Split, Transaction


def create_transaction(title, src, dst, amount, type, date=date.today(), category=None):
    t = Transaction.objects.create(title=title, date=date, transaction_type=type,
                                   src=src, dst=dst, amount=amount)
    Split.objects.bulk_create([
        Split(title=title, account=src, opposing_account=dst,
              amount=-amount, transaction=t, date=date, category=category),
        Split(title=title, account=dst, opposing_account=src,
              amount=amount, transaction=t, date=date, category=category)])
    t.save()
    return t

def create_transaction_without_split(title, src, dst, amount, type, date=date.today(), category=None):
    t = Transaction.objects.create(title=title, date=date, transaction_type=type,
                                   src=src, dst=dst, amount=amount)
    t.save()
    return t

def create_transaction_with_splits(title, src, dst, amount, type, splits, date=date.today(), category=None):
    t = Transaction.objects.create(title=title, date=date, transaction_type=type,
                                   src=src, dst=dst, amount=amount)

    for s in splits:
        s.transaction = t

    Split.objects.bulk_create(splits)

    t.save()
    return t


def create_account(name, account_type=AccountType.PERSONAL):
    return Account.objects.create(name=name, account_type=account_type)
