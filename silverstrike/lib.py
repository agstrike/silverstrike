import csv
import datetime

from .models import Account, Category, ImportConfiguration, Transaction, TransactionJournal


def last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
    return next_month - datetime.timedelta(days=next_month.day)


def import_csv(path, config):
    data = []
    col_types = [int(x) for x in config.config.split(' ')]
    for line in csv.reader(open(path)):
        entry = dict()
        for i in range(len(line)):
            if col_types[i] == ImportConfiguration.SOURCE_ACCOUNT:
                entry['src'] = line[i]
            elif col_types[i] == ImportConfiguration.DESTINATION_ACCOUNT:
                entry['dst'] = line[i]
            elif col_types[i] == ImportConfiguration.AMOUNT:
                entry['amount'] = line[i]
            elif col_types[i] == ImportConfiguration.DATE:
                entry['date'] = line[i]
            elif col_types[i] == ImportConfiguration.NOTES:
                entry['notes'] = line[i]
            elif col_types[i] == ImportConfiguration.CATEGORY:
                entry['category'] = line[i]
            elif col_types[i] == ImportConfiguration.TITLE:
                entry['title'] = line[i]
        data.append(entry)

    if config.headers:
        del data[0]
    accounts = dict()
    for name, id in Account.objects.all().values_list('name', 'id'):
        accounts[name] = id

    # create objects
    for e in data:
        if e['src'] in accounts:
            e['src'] = accounts[e['src']]
        else:
            e['src'] = Account.objects.create(name=e['src']).id
        if e['dst'] in accounts:
            e['dst'] = accounts[e['dst']]
        else:
            e['dst'] = Account.objects.create(name=e['src']).id

        j = TransactionJournal.objects.create(title=e['title'], date=e['date'], notes=e['notes'])
        Transaction.objects.create(account=e['src'], opposing_account=e['dst'],
                                   journal=j, amount=e['amount'])
        Transaction.objects.create(account=e['dst'], opposing_account=e['src'],
                                   journal=j, amount=-float(e['amount']))


def import_firefly(csv_file):
    # journal_id = 0
    date = 1
    description = 2
    # currency_code = 3
    amount = 4
    transaction_type = 5
    # source_account_id = 6
    source_account_name = 7
    # destination_account_id = 8
    destination_account_name = 9
    # budget_id = 10
    # budget_name = 11
    # category_id = 12
    category_name = 13

    system_account, _ = Account.objects.get_or_create(name='system', account_type=Account.SYSTEM)

    personal_accounts = dict()
    foreign_accounts = dict()
    for name, id, t in Account.objects.all().values_list('name', 'id', 'account_type'):
        if t == Account.PERSONAL:
            personal_accounts[name] = id
        else:
            foreign_accounts[name] = id

    categories = dict()
    for name, id in Category.objects.all().values_list('name', 'id'):
        categories[name] = id

    first_time = True
    for line in csv.reader(open(csv_file)):
        if first_time:
            first_time = False
            continue
        if line[source_account_name] in personal_accounts:
                line[source_account_name] = personal_accounts[line[source_account_name]]
        else:
            a = Account.objects.create(name=line[source_account_name],
                                       account_type=Account.PERSONAL)
            personal_accounts[a.name] = a.id
            line[source_account_name] = a.id

        line[amount] = float(line[amount])

        if line[transaction_type] == 'Withdrawal':
            t_type = TransactionJournal.WITHDRAW
            if line[destination_account_name] in foreign_accounts:
                line[destination_account_name] = foreign_accounts[line[destination_account_name]]
            else:
                a = Account.objects.create(name=line[destination_account_name],
                                           account_type=Account.FOREIGN)
                foreign_accounts[a.name] = a.id
                line[destination_account_name] = a.id

        elif line[transaction_type] == 'Transfer':
            # positive transfers are wrong
            if line[amount] > 0:
                continue
            t_type = TransactionJournal.TRANSFER
            if line[destination_account_name] in personal_accounts:
                line[destination_account_name] = personal_accounts[line[destination_account_name]]
            else:
                a = Account.objects.create(name=line[destination_account_name],
                                           account_type=Account.PERSONAL)
                personal_accounts[a.name] = a.id
                line[destination_account_name] = a.id

        elif line[transaction_type] == 'Deposit':
            t_type = TransactionJournal.DEPOSIT
            if line[destination_account_name] in foreign_accounts:
                line[destination_account_name] = foreign_accounts[line[destination_account_name]]
            else:
                a = Account.objects.create(name=line[destination_account_name],
                                           account_type=Account.FOREIGN)
                foreign_accounts[a.name] = a.id
                line[destination_account_name] = a.id
        elif line[transaction_type] == 'Opening balance':
            line[destination_account_name] = system_account.id

        if line[category_name] in categories:
            line[category_name] = categories[line[category_name]]
        elif line[category_name]:
            c = Category.objects.create(name=line[category_name])
            categories[c.name] = c.id
            line[category_name] = c.id
        else:
            line[category_name] = None
        line[date] = datetime.datetime.strptime(line[date], '%Y-%m-%d')

        journal = TransactionJournal.objects.create(
            title=line[description], date=line[date],
            transaction_type=t_type, category_id=line[category_name])
        Transaction.objects.bulk_create(
            [Transaction(account_id=line[source_account_name],
                         opposing_account_id=line[destination_account_name],
                         amount=line[amount], journal_id=journal.id),
             Transaction(account_id=line[destination_account_name],
                         opposing_account_id=line[source_account_name],
                         amount=-line[amount], journal_id=journal.id)])
