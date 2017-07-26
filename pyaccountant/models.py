from datetime import date, timedelta

from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext as _


class AccountType(models.Model):
    name = models.CharField(max_length=64, unique=True)
    creatable = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Account(models.Model):
    PERSONAL = 1
    REVENUE = 2
    EXPENSE = 3
    ACCOUNT_TYPES = (
        (PERSONAL, _('Personal')),
        (REVENUE, _('Revenue')),
        (EXPENSE, _('Expense')),
    )

    name = models.CharField(max_length=64)
    internal_type = models.IntegerField(choices=ACCOUNT_TYPES, default=PERSONAL)
    account_type = models.ForeignKey(AccountType, models.CASCADE, null=True)
    active = models.BooleanField(default=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def balance(self):
        return Transaction.objects.filter(account=self).aggregate(
            models.Sum('amount'))['amount__sum'] or 0

    def balance_on(self, date):
        return Transaction.objects.filter(account=self, journal__date__lte=date).aggregate(
            models.Sum('amount'))['amount__sum'] or 0

    def get_absolute_url(self):
        return reverse('account_transactions', kwargs={'pk': self.pk})

    def get_data_points(self, dstart=date.today() - timedelta(days=365),
                        dend=date.today(), steps=50):
        step = (dend - dstart) / steps
        data_points = []
        for i in range(steps):
            balance = self.balance_on(dstart)
            data_points.append((dstart, balance))
            dstart += step
        return data_points


class TransactionJournal(models.Model):
    DEPOSIT = 1
    WITHDRAW = 2
    TRANSFER = 3
    SYSTEM = 4
    TRANSACTION_TYPES = (
        (DEPOSIT, 'Deposit'),
        (WITHDRAW, 'Withdrawl'),
        (TRANSFER, 'Transfer'),
        (SYSTEM, 'SYSTEM'),
    )

    title = models.CharField(max_length=64)
    date = models.DateField(default=date.today)
    notes = models.TextField(blank=True)
    category = models.ForeignKey('Category', related_name='transactions', blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)
    transaction_type = models.IntegerField(choices=TRANSACTION_TYPES)

    def __str__(self):
        return '{}:{} @ {}'.format(self.pk, self.title, self.date)


class Transaction(models.Model):
    account = models.ForeignKey(Account, models.CASCADE)
    opposing_account = models.ForeignKey(Account, models.CASCADE,
                                         related_name='opposing_transactions')
    journal = models.ForeignKey(TransactionJournal, models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return '{} -> {}'.format(self.journal, self.amount)


class CategoryGroup(models.Model):
    name = models.CharField(max_length=64)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=64)
    group = models.ForeignKey(CategoryGroup)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def money_spent(self):
        return abs(Transaction.objects.filter(
                journal__category=self, account__internal_type=Account.PERSONAL,
                journal__transaction_type=TransactionJournal.WITHDRAW).aggregate(
            models.Sum('amount'))['amount__sum'] or 0)
