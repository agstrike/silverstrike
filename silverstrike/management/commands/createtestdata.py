from datetime import date
from random import randrange

from dateutil.relativedelta import relativedelta

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from silverstrike.models import Account, Category, RecurringTransaction, Split, Transaction


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--prune', action='store_true',
                            help='Clears all data before inserting new objects')

    def handle(self, *args, **options):
        if options['prune']:
            self._prune()
        self._initialize()
        today = date.today()
        try:
            start_date = Transaction.objects.filter(
                date__lte=today).latest('date').date.replace(day=1)
        except ObjectDoesNotExist:
            start_date = date(2016, 1, 1)

        while start_date < today:
            self._create_monthly(start_date.year, start_date.month)
            start_date += relativedelta(months=+1)
        Transaction.objects.bulk_create(self.transactions)
        Split.objects.bulk_create(self.splits)

    def _prune(self):
        Account.objects.exclude(account_type=Account.AccountType.SYSTEM).delete()
        Category.objects.all().delete()
        RecurringTransaction.objects.all().delete()
        Transaction.objects.all().delete()
        Split.objects.all().delete()

    def _initialize(self):
        D = Transaction.DEPOSIT
        W = Transaction.WITHDRAW
        T = Transaction.TRANSFER
        self.transactions = []
        self.splits = []
        self.counter = 100
        self.work, _ = Account.objects.get_or_create(
            name='Work',
            account_type=Account.AccountType.FOREIGN)

        self.checking, _ = Account.objects.get_or_create(name='Checking', show_on_dashboard=True)
        self.savings, _ = Account.objects.get_or_create(name='Savings', show_on_dashboard=True)

        self.landlord, _ = Account.objects.get_or_create(
            name='Landlord', account_type=Account.AccountType.FOREIGN)
        self.supermarket, _ = Account.objects.get_or_create(
            name='Supermarket', account_type=Account.AccountType.FOREIGN)
        self.insurer, _ = Account.objects.get_or_create(
            name='Insurnace', account_type=Account.AccountType.FOREIGN)
        self.club, _ = Account.objects.get_or_create(
            name='Club',
            account_type=Account.AccountType.FOREIGN)

        self.home, _ = Category.objects.get_or_create(name='Home')
        self.groceries, _ = Category.objects.get_or_create(name='Groceries')
        self.insurance, _ = Category.objects.get_or_create(name='Insurance')
        self.leisure, _ = Category.objects.get_or_create(name='Leisure')
        self.income_category, _ = Category.objects.get_or_create(name='Income')

        self.income, _ = RecurringTransaction.objects.update_or_create(
            title='Income', src=self.work, dst=self.checking,
            defaults={'interval': RecurringTransaction.MONTHLY,
                      'transaction_type': D, 'category': self.home, 'amount': 2000,
                      'date': (date.today() + relativedelta(months=+1)).replace(day=1)})
        self.rent, _ = RecurringTransaction.objects.update_or_create(
            title='Rent', src=self.checking, dst=self.landlord,
            defaults={'interval': RecurringTransaction.MONTHLY,
                      'transaction_type': W, 'category': self.home, 'amount': 900,
                      'date': (date.today() + relativedelta(months=+1)).replace(day=2)})
        self.insurnace_r, _ = RecurringTransaction.objects.update_or_create(
            title='Insurance', src=self.checking, dst=self.insurer,
            defaults={'interval': RecurringTransaction.MONTHLY,
                      'transaction_type': W, 'category': self.insurance, 'amount': 170,
                      'date': (date.today() + relativedelta(months=+1)).replace(day=15)})

        self.MONTHLY = [
            ('Income', [1], self.work, self.checking, [2200, 2201], self.income_category,
             D, self.income),
            ('Rent', [2], self.checking, self.landlord, [1000, 1001], self.home, W, self.rent),
            ('Saving', [27], self.checking, self.savings, [150, 200], None, T, None),
            ('Groceries', [3, 10, 17, 26], self.checking, self.supermarket,
             [80, 150], self.groceries, W, None),
            ('Insurance', [15], self.checking, self.insurer, [300, 301], self.insurance, W,
             self.insurnace_r),
            ('Clubbing', [15, 25], self.checking, self.club, [80, 120], self.leisure, W,
             None),
        ]

    def _create_monthly(self, year, month):
        for title, days, src, dst, amountRange, category, type, recurrence in self.MONTHLY:
            for day in days:
                amount = randrange(amountRange[0], amountRange[1])
                transaction_date = date(year, month, day)
                if transaction_date > date.today():
                    continue
                self.transactions.append(Transaction(
                    src=src, dst=dst,
                    title=title, date=transaction_date, id=self.counter,
                    transaction_type=type, recurrence=recurrence))
                self.splits.append(Split(
                    account=src, opposing_account=dst, transaction_id=self.counter,
                    amount=-amount, category=category, date=transaction_date, title=title))
                self.splits.append(Split(
                    account=dst, opposing_account=src, transaction_id=self.counter,
                    amount=amount, category=category, date=transaction_date, title=title))
                self.counter += 1
