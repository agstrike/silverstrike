import uuid

from datetime import date, timedelta

from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext as _


class Account(models.Model):
    PERSONAL = 1
    REVENUE = 2
    EXPENSE = 3
    SYSTEM = 4
    ACCOUNT_TYPES = (
        (PERSONAL, _('Personal')),
        (REVENUE, _('Revenue')),
        (EXPENSE, _('Expense')),
        (SYSTEM, _('System')),
    )

    name = models.CharField(max_length=64)
    internal_type = models.IntegerField(choices=ACCOUNT_TYPES, default=PERSONAL)
    active = models.BooleanField(default=True)
    last_modified = models.DateTimeField(auto_now=True)
    show_on_dashboard = models.BooleanField(default=False)

    class Meta:
        ordering = ['-show_on_dashboard', 'name']

    def __str__(self):
        return self.name

    @property
    def transaction_num(self):
        return Transaction.objects.filter(account=self).count()

    @property
    def balance(self):
        return Transaction.objects.filter(account=self).aggregate(
            models.Sum('amount'))['amount__sum'] or 0

    def balance_on(self, date):
        return Transaction.objects.filter(account=self, journal__date__lte=date).aggregate(
            models.Sum('amount'))['amount__sum'] or 0

    def get_absolute_url(self):
        return reverse('account_detail',
                       kwargs={'pk': self.pk, 'dstart': date.today().replace(day=1)})

    def get_data_points(self, dstart=date.today() - timedelta(days=365),
                        dend=date.today(), steps=30):
        step = (dend - dstart) / steps
        if step < timedelta(days=1):
            step = timedelta(days=1)
            steps = int((dend - dstart) / step)
        data_points = []
        balance = self.balance_on(dstart)
        transactions = list(Transaction.objects.prefetch_related('journal').filter(
            account_id=self.pk, journal__date__gt=dstart,
            journal__date__lte=dend).order_by('-journal__date'))
        for i in range(steps):
            while len(transactions) > 0 and transactions[-1].journal.date <= dstart.date():
                t = transactions.pop()
                balance += t.amount
            data_points.append((dstart, balance))
            dstart += step
        for t in transactions:
            balance += t.amount
        data_points.append((dend, balance))
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
    bill = models.ForeignKey('RecurringTransaction', blank=True, null=True)

    def __str__(self):
        return '{}:{} @ {}'.format(self.pk, self.title, self.date)

    def get_absolute_url(self):
        return reverse('transaction_update', args=[self.pk])


class Transaction(models.Model):
    account = models.ForeignKey(Account, models.CASCADE)
    opposing_account = models.ForeignKey(Account, models.CASCADE,
                                         related_name='opposing_transactions')
    journal = models.ForeignKey(TransactionJournal, models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return '{} -> {}'.format(self.journal, self.amount)

    @property
    def is_transfer(self):
        return self.journal.transaction_type == TransactionJournal.TRANSFER

    @property
    def is_withdraw(self):
        return self.journal.transaction_type == TransactionJournal.WITHDRAW

    @property
    def is_deposit(self):
        return self.journal.transaction_type == TransactionJournal.DEPOSIT


class Category(models.Model):
    name = models.CharField(max_length=64)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def money_spent(self):
        return abs(Transaction.objects.filter(
                journal__category=self, account__internal_type=Account.PERSONAL,
                journal__transaction_type=TransactionJournal.WITHDRAW).aggregate(
            models.Sum('amount'))['amount__sum'] or 0)


class ImportFile(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='imports')


class ImportConfiguration(models.Model):
    DO_NOT_USE = 0
    SOURCE_ACCOUNT = 1
    DESTINATION_ACCOUNT = 2
    AMOUNT = 3
    DATE = 4
    NOTES = 5
    CATEGORY = 6
    TITLE = 7

    FIELD_TYPES = (
        (DO_NOT_USE, _('Do not use')),
        (SOURCE_ACCOUNT, _('Source Account')),
        (DESTINATION_ACCOUNT, _('Destination Account')),
        (AMOUNT, _('Amount')),
        (DATE, _('Date')),
        (NOTES, _('Notes')),
        (CATEGORY, _('Category')),
        )

    name = models.CharField(max_length=64)
    headers = models.BooleanField(help_text=_('First line contains headers'))
    default_account = models.ForeignKey(Account,
                                        limit_choices_to={'internal_type': Account.PERSONAL},
                                        null=True, blank=True)
    config = models.TextField()

    def __str__(self):
        return self.name


class RecurringTransaction(models.Model):
    WEEKLY = 1
    MONTHLY = 2
    YEARLY = 3
    RECCURENCE_OPTIONS = ((WEEKLY, _('Weekly')),
        (MONTHLY, _('Monthly')),
        (YEARLY, _('Yearly')))

    title = models.CharField(max_length=64)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    src = models.ForeignKey(Account)
    dst = models.ForeignKey(Account, related_name='opposing_recurring_transactions')
    recurrence = models.IntegerField(choices=RECCURENCE_OPTIONS)

    def __str__(self):
        return '{}({}) due on {}'.format(self.title, self.amount, self.date)

    @property
    def is_due(self):
        return date.today() > self.date

    @property
    def get_recurrence(self):
        for r, name in self.RECCURENCE_OPTIONS:
            if r == self.recurrence:
                return name
        return ''
