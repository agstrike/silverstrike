from datetime import date
from random import randrange

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from silverstrike.models import Account, Category, Journal, Split


def _create_transaction(date, amount, src, dst, title, category, type):
    journal = Journal.objects.create(title=title, date=date,
                                     transaction_type=type)
    Split.objects.create(account=src, opposing_account=dst, journal=journal,
                         amount=-amount, category=category)
    Split.objects.create(account=dst, opposing_account=src, journal=journal,
                         amount=amount, category=category)


class Command(BaseCommand):
    def handle(self, *args, **options):
        self._initialize()
        try:
            past = Journal.objects.latest('date')
            start_month = past.date.month + 1
            start_year = past.date.year
            if start_month == 13:
                start_year += 1
        except ObjectDoesNotExist:
            start_year = 2016
            start_month = 1

        today = date.today()
        for y in range(start_year, today.year + 1):
            if y == start_year and y == today.year:
                self._create_yearly(y, start_month, today.month)
            if y == start_year:
                self._create_yearly(y, start_month, 13)
            elif y == today.year:
                self._create_yearly(y, 1, today.month)
            else:
                self._create_yearly(y, 1, 13)

    def _initialize(self):
        D = Journal.DEPOSIT
        W = Journal.WITHDRAW
        T = Journal.TRANSFER
        self.work, _ = Account.objects.get_or_create(name='work', account_type=Account.REVENUE)

        self.checking, _ = Account.objects.get_or_create(name='checking', show_on_dashboard=True)
        self.savings, _ = Account.objects.get_or_create(name='savings', show_on_dashboard=True)

        self.landlord, _ = Account.objects.get_or_create(
            name='landlord', account_type=Account.EXPENSE)
        self.supermarket, _ = Account.objects.get_or_create(
            name='supermarket', account_type=Account.EXPENSE)
        self.insurer, _ = Account.objects.get_or_create(
            name='insurnace', account_type=Account.EXPENSE)
        self.club, _ = Account.objects.get_or_create(name='club', account_type=Account.EXPENSE)

        self.home, _ = Category.objects.get_or_create(name='home')
        self.groceries, _ = Category.objects.get_or_create(name='groceries')
        self.insurance, _ = Category.objects.get_or_create(name='insurance')
        self.leisure, _ = Category.objects.get_or_create(name='leisure')

        self.YEARLY = [
            ('special expense', [2, 4, 6, 8, 10, 12], self.checking, self.supermarket,
             [100, 500], self.groceries, W),
        ]

        self.MONTHLY = [
            ('income', [1], self.work, self.checking, [2000, 3000], None, D),
            ('rent', [2], self.checking, self.landlord, [900, 901], self.home, W),
            ('saving', [26], self.checking, self.savings, [100, 500], None, T),
            ('groceries', [1, 5, 10, 15, 20, 25, 27], self.checking, self.supermarket,
             [50, 100], self.groceries, W),
            ('insurance', [15], self.checking, self.insurer, [70, 200], self.insurance, W),
            ('clubbing', [3, 8, 17, 22, 27], self.checking, self.club, [20, 100], self.leisure, W),
        ]

    def _create_monthly(self, year, month):
        for title, days, src, dst, amountRange, category, type in self.MONTHLY:
            for day in days:
                amount = randrange(amountRange[0], amountRange[1])
                _create_transaction(date(year, month, day), amount, src, dst, title, category, type)

    def _create_yearly(self, year, start, end):
        for title, months, src, dst, amountRange, category, type in self.YEARLY:
            for m in range(start, end):
                self._create_monthly(year, m)
                if m in months:
                    amount = randrange(amountRange[0], amountRange[1])
                    _create_transaction(date(year, m, 1), amount, src, dst, title, category, type)
