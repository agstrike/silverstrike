import csv
import datetime

from silverstrike.models import Account, Category, ImportConfiguration, Split, Transaction


def last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
    return next_month - datetime.timedelta(days=next_month.day)


def import_csv(path, config):
    data = []
    col_types = [int(x) for x in config.config.split(' ')]
    with open(path) as csv_file:
        for line in csv.reader(csv_file):
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

        j = Transaction.objects.create(title=e['title'], date=e['date'], notes=e['notes'])
        Split.objects.create(account=e['src'], opposing_account=e['dst'],
                             transaction=j, amount=e['amount'], date=e['date'])
        Split.objects.create(account=e['dst'], opposing_account=e['src'],
                             transaction=j, amount=-float(e['amount']), date=e['date'])


def import_firefly(csv_path):
    date = 'date'
    title = 'description'
    amount = 'amount'
    source = 'asset_account_name'
    destination = 'opposing_account_name'
    category = 'category_name'
    notes = 'notes'
    transaction_type = 'transaction_type'

    system_account, _ = Account.objects.get_or_create(account_type=Account.SYSTEM,
                                                      defaults={'name': 'System Account'})

    personal_accounts = dict()
    foreign_accounts = dict()
    for name, id, t in Account.objects.all().values_list('name', 'id', 'account_type'):
        if t == Account.PERSONAL:
            personal_accounts[name] = id
        elif t == Account.FOREIGN:
            foreign_accounts[name] = id

    categories = dict()
    for name, id in Category.objects.all().values_list('name', 'id'):
        categories[name] = id

    first_time = True
    with open(csv_path) as csv_file:
        for line in csv.reader(csv_file):
            if first_time:
                first_time = False
                line = {k: v for v, k in enumerate(line)}
                date = line[date]
                title = line[title]
                amount = line[amount]
                transaction_type = line[transaction_type]
                source = line[source]
                destination = line[destination]
                category = line[category]
                notes = line[notes]
                continue
            if line[source] in personal_accounts:
                    line[source] = personal_accounts[line[source]]
            else:
                a = Account.objects.create(name=line[source],
                                           account_type=Account.PERSONAL)
                personal_accounts[a.name] = a.id
                line[source] = a.id

            line[amount] = float(line[amount])

            if line[transaction_type] == 'Withdrawal':
                t_type = Transaction.WITHDRAW
                if line[destination] in foreign_accounts:
                    line[destination] = foreign_accounts[line[destination]]
                else:
                    a = Account.objects.create(name=line[destination],
                                               account_type=Account.FOREIGN)
                    foreign_accounts[a.name] = a.id
                    line[destination] = a.id

            elif line[transaction_type] == 'Transfer':
                # positive transfers are wrong
                if line[amount] > 0:
                    continue
                t_type = Transaction.TRANSFER
                if line[destination] in personal_accounts:
                    line[destination] = personal_accounts[line[destination]]
                else:
                    a = Account.objects.create(name=line[destination],
                                               account_type=Account.PERSONAL)
                    personal_accounts[a.name] = a.id
                    line[destination] = a.id

            elif line[transaction_type] == 'Deposit':
                t_type = Transaction.DEPOSIT
                if line[destination] in foreign_accounts:
                    line[destination] = foreign_accounts[line[destination]]
                else:
                    a = Account.objects.create(name=line[destination],
                                               account_type=Account.FOREIGN)
                    foreign_accounts[a.name] = a.id
                    line[destination] = a.id
            elif line[transaction_type] == 'Opening balance':
                line[destination] = system_account.id

            if line[category] in categories:
                line[category] = categories[line[category]]
            elif line[category]:
                c = Category.objects.create(name=line[category])
                categories[c.name] = c.id
                line[category] = c.id
            else:
                line[category] = None
            line[date] = datetime.datetime.strptime(line[date], '%Y%m%d')

            transaction = Transaction.objects.create(
                title=line[title], date=line[date],
                transaction_type=t_type)
            Split.objects.bulk_create(
                [Split(account_id=line[source], title=line[title],
                       date=line[date],
                       opposing_account_id=line[destination], amount=line[amount],
                       transaction_id=transaction.id, category_id=line[category]),
                 Split(account_id=line[destination], title=line[title],
                       date=line[date],
                       opposing_account_id=line[source], amount=-line[amount],
                       transaction_id=transaction.id, category_id=line[category])])
