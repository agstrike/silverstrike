from pyaccountant.models import Account, AccountType, Category, CategoryGroup, Transaction, TransactionJournal
from datetime import timedelta, date
from random import randrange


def _create_transaction(date, amount, src, dst, title, category):
    journal = TransactionJournal.objects.create(title=title, date=date, category=category)
    Transaction.objects.create(account=src, opposing_account=dst, journal=journal, amount=-amount)
    Transaction.objects.create(account=dst, opposing_account=src, journal=journal, amount=amount)


class TestData():
    def __init__(self):
        self.work, _ = Account.objects.get_or_create(name='work', internal_type=Account.REVENUE)

        self.checking, _ = Account.objects.get_or_create(name='checking')
        self.savings, _ = Account.objects.get_or_create(name='savings')

        self.landlord, _ = Account.objects.get_or_create(name='landlord', internal_type=Account.EXPENSE)
        self.supermarket, _ = Account.objects.get_or_create(name='supermarket', internal_type=Account.EXPENSE)
        self.insurer, _ = Account.objects.get_or_create(name='insurnace', internal_type=Account.EXPENSE)
        self.club, _ = Account.objects.get_or_create(name='club', internal_type=Account.EXPENSE)

        self.group, _ = CategoryGroup.objects.get_or_create(name='all')
        self.home, _ = Category.objects.get_or_create(name='home', group=self.group)
        self.groceries, _ = Category.objects.get_or_create(name='groceries', group=self.group)
        self.insurance, _ = Category.objects.get_or_create(name='insurance', group=self.group)
        self.leisure, _ = Category.objects.get_or_create(name='leisure', group=self.group)

        self.YEARLY = [
            ('special expense', [2, 4, 6, 8, 10, 12], self.checking, self.supermarket, [100, 500], self.groceries),
        ]

        self.MONTHLY = [
            ('income', [1], self.work, self.checking, [2000, 3000], None),
            ('rent', [2], self.checking, self.landlord, [900, 901], self.home),
            ('saving', [26], self.checking, self.savings, [100,500], None),
            ('groceries', [1, 5, 10, 15, 20, 25, 27], self.checking, self.supermarket, [50,100], self.groceries),
            ('insurance', [15], self.checking, self.insurer, [70,200], self.insurance),
            ('clubbing', [3,8,17,22,27], self.checking, self.club, [20,100], self.leisure),
        ]

    def create_monthly(self, month, year):
        for title, days, src, dst, amountRange, category in self.MONTHLY:
            for day in days:
                amount = randrange(amountRange[0], amountRange[1])
                _create_transaction(date(year, month, day), amount, src, dst, title, category)

    def create_yearly(self, year):
        for title, months, src, dst, amountRange, category in self.YEARLY:
            for month in months:
                amount = randrange(amountRange[0], amountRange[1])
                _create_transaction(date(year, month, 1), amount, src, dst, title, category)

    def do(self):
        for i in range(2016, 2018):
            self.create_yearly(i)
            for j in range(1, 13):
                self.create_monthly(j, i)
