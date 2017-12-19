from datetime import date
from random import randrange

from dateutil.relativedelta import relativedelta

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from silverstrike.models import Account, Category, RecurringTransaction, Split, Transaction


def _create_transaction(date, amount, src, dst, title, category, type, recurrence):
    transaction = Transaction.objects.create(title=title, date=date,
                                             transaction_type=type,
                                             recurrence=recurrence)
    Split.objects.create(account=src, opposing_account=dst, transaction=transaction,
                         amount=-amount, category=category, date=date, title=title)
    Split.objects.create(account=dst, opposing_account=src, transaction=transaction,
                         amount=amount, category=category, date=date, title=title)


class Command(BaseCommand):
    def handle(self, *args, **options):
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

    def _initialize(self):
        D = Transaction.DEPOSIT
        W = Transaction.WITHDRAW
        T = Transaction.TRANSFER
        self.work, _ = Account.objects.get_or_create(name='work', account_type=Account.FOREIGN)

        self.checking, _ = Account.objects.get_or_create(name='checking', show_on_dashboard=True)
        self.savings, _ = Account.objects.get_or_create(name='savings', show_on_dashboard=True)

        self.landlord, _ = Account.objects.get_or_create(
            name='landlord', account_type=Account.FOREIGN)
        self.supermarket, _ = Account.objects.get_or_create(
            name='supermarket', account_type=Account.FOREIGN)
        self.insurer, _ = Account.objects.get_or_create(
            name='insurnace', account_type=Account.FOREIGN)
        self.club, _ = Account.objects.get_or_create(name='club', account_type=Account.FOREIGN)

        self.home, _ = Category.objects.get_or_create(name='home')
        self.groceries, _ = Category.objects.get_or_create(name='groceries')
        self.insurance, _ = Category.objects.get_or_create(name='insurance')
        self.leisure, _ = Category.objects.get_or_create(name='leisure')

        self.rent, _ = RecurringTransaction.objects.update_or_create(
            title='rent', src=self.checking, dst=self.landlord,
            defaults={'recurrence': RecurringTransaction.MONTHLY,
                      'transaction_type': W, 'category': self.home, 'amount': 900,
                      'date': (date.today() + relativedelta(months=+1)).replace(day=2)})
        self.insurnace_r, _ = RecurringTransaction.objects.update_or_create(
            title='insurance', src=self.checking, dst=self.insurer,
            defaults={'recurrence': RecurringTransaction.MONTHLY,
                      'transaction_type': W, 'category': self.insurance, 'amount': 70,
                      'date': (date.today() + relativedelta(months=+1)).replace(day=15)})

        self.MONTHLY = [
            ('income', [1], self.work, self.checking, [2500, 3000], None, D, None),
            ('rent', [2], self.checking, self.landlord, [900, 901], self.home, W, self.rent),
            ('saving', [27], self.checking, self.savings, [50, 200], None, T, None),
            ('groceries', [1, 5, 10, 13, 15, 20, 21, 25, 27], self.checking, self.supermarket,
             [50, 100], self.groceries, W, None),
            ('insurance', [15], self.checking, self.insurer, [70, 200], self.insurance, W,
             self.insurnace_r),
            ('clubbing', [3, 8, 17, 22, 27], self.checking, self.club, [20, 100], self.leisure, W,
             None),
        ]

    def _create_monthly(self, year, month):
        for title, days, src, dst, amountRange, category, type, recurrence in self.MONTHLY:
            for day in days:
                amount = randrange(amountRange[0], amountRange[1])
                _create_transaction(date(year, month, day), amount, src, dst,
                                    title, category, type, recurrence)
