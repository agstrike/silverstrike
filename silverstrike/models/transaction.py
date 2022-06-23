
from datetime import date

from django.db import models
from django.urls import reverse

from .account_type import AccountType


class TransactionQuerySet(models.QuerySet):
    def last_10(self):
        return self.order_by('-date')[:10]

    def date_range(self, dstart, dend):
        return self.filter(date__gte=dstart, date__lte=dend)


class Transaction(models.Model):
    DEPOSIT = 1
    WITHDRAW = 2
    TRANSFER = 3
    SYSTEM = 4
    TRANSACTION_TYPES = (
        (DEPOSIT, 'Deposit'),
        (WITHDRAW, 'Withdrawal'),
        (TRANSFER, 'Transfer'),
        (SYSTEM, 'Reconcile'),
    )

    class Meta:
        ordering = ['-date', 'title']

    title = models.CharField(max_length=64)
    date = models.DateField(default=date.today)
    notes = models.TextField(blank=True, null=True)
    transaction_type = models.IntegerField(choices=TRANSACTION_TYPES)
    src = models.ForeignKey('Account', models.CASCADE, 'debits')
    dst = models.ForeignKey('Account', models.CASCADE, 'credits')
    amount = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    last_modified = models.DateTimeField(auto_now=True)
    recurrence = models.ForeignKey('RecurringTransaction', models.SET_NULL,
                                   related_name='recurrences', blank=True, null=True)

    objects = TransactionQuerySet.as_manager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('transaction_detail', args=[self.pk])

    def get_transaction_type_str(self):
        for i, name in self.TRANSACTION_TYPES:
            if i == self.transaction_type:
                return name

    @property
    def is_split(self):
        return len(self.splits.all()) > 2

    @property
    def is_system(self):
        return self.transaction_type == self.SYSTEM

    @property
    def is_transfer(self):
        return self.transaction_type == self.TRANSFER

    @property
    def is_withdraw(self):
        return self.transaction_type == self.WITHDRAW

    @property
    def is_deposit(self):
        return self.transaction_type == self.DEPOSIT


class SplitQuerySet(models.QuerySet):
    def personal(self):
        return self.filter(account__account_type=AccountType.PERSONAL)

    def income(self):
        return self.filter(opposing_account__account_type=AccountType.FOREIGN, amount__gt=0)

    def expense(self):
        return self.filter(opposing_account__account_type=AccountType.FOREIGN, amount__lt=0)

    def personal_dashboard(self):
        return self.filter(account__account_type=AccountType.PERSONAL,
                           account__show_on_dashboard=True)

    def date_range(self, dstart, dend):
        return self.filter(date__gte=dstart, date__lte=dend)

    def category(self, category):
        return self.filter(category=category)

    def transfers_once(self):
        return self.exclude(
            opposing_account__account_type=AccountType.PERSONAL,
            amount__gte=0)

    def exclude_transfers(self):
        return self.exclude(account__account_type=AccountType.PERSONAL,
                            opposing_account__account_type=AccountType.PERSONAL)

    def upcoming(self):
        return self.filter(date__gt=date.today())

    def past(self):
        return self.filter(date__lte=date.today())

    def recurrence(self, recurrence_id):
        return self.filter(transaction__recurrence_id=recurrence_id)


class Split(models.Model):
    account = models.ForeignKey('Account', models.CASCADE, related_name='incoming_transactions')
    opposing_account = models.ForeignKey('Account', models.CASCADE,
                                         related_name='outgoing_transactions')
    title = models.CharField(max_length=64)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=date.today)
    category = models.ForeignKey('Category', models.SET_NULL, blank=True, null=True,
                                 related_name='splits')
    transaction = models.ForeignKey(Transaction, models.CASCADE, related_name='splits',
                                    blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = SplitQuerySet.as_manager()

    class Meta:
        ordering = ['-date', 'title']

    def __str__(self):
        return self.title

    @property
    def is_transfer(self):
        return self.transaction.transaction_type == Transaction.TRANSFER

    @property
    def is_withdraw(self):
        return self.transaction.transaction_type == Transaction.WITHDRAW

    @property
    def is_deposit(self):
        return self.transaction.transaction_type == Transaction.DEPOSIT

    @property
    def is_system(self):
        return self.transaction.transaction_type == Transaction.SYSTEM

    def get_absolute_url(self):
        return self.transaction.get_absolute_url()
