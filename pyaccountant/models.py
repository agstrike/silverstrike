import enum

from datetime import date

from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext as _


class InternalAccountType(enum.Enum):
    personal = 1
    revenue = 2
    expense = 3


class AccountType(models.Model):
    name = models.CharField(max_length=64)
    creatable = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Currency(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Account(models.Model):
    name = models.CharField(max_length=64)
    currency = models.ForeignKey('Currency', models.SET_NULL, null=True)
    internal_type = models.IntegerField(choices=[
        (InternalAccountType.personal.value, _('Personal')),
        (InternalAccountType.revenue.value, _('Revenue')),
        (InternalAccountType.expense.value, _('Expense'))],
        default=InternalAccountType.personal.value)
    account_type = models.ForeignKey(AccountType, models.CASCADE, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @property
    def balance(self):
        return Transaction.objects.filter(account=self).aggregate(
            models.Sum('amount'))['amount__sum'] or 0

    def get_absolute_url(self):
        return reverse('account_detail', kwargs={'pk': self.pk})


class TransactionJournal(models.Model):
    title = models.CharField(max_length=64)
    date = models.DateField(default=date.today)
    notes = models.TextField(blank=True)

    def __str__(self):
        return '{}:{} @ {}'.format(self.pk, self.title, self.date)


class Transaction(models.Model):
    account = models.ForeignKey(Account, models.CASCADE)
    journal = models.ForeignKey(TransactionJournal, models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return '{} -> {}'.format(self.journal, self.amount)
