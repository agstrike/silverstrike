import uuid
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _


class AccountQuerySet(models.QuerySet):
    def personal(self):
        return self.filter(account_type=Account.AccountType.PERSONAL)

    def foreign(self):
        return self.filter(account_type=Account.AccountType.FOREIGN)

    def active(self):
        return self.filter(active=True)

    def inactive(self):
        return self.filter(active=False)

    def shown_on_dashboard(self):
        return self.filter(show_on_dashboard=True)


class Account(models.Model):
    class AccountType(models.IntegerChoices):
        PERSONAL = 1, _('Personal')
        FOREIGN = 2, _('Foreign')
        SYSTEM = 3, _('System')

    name = models.CharField(max_length=64)
    account_type = models.IntegerField(choices=AccountType.choices, default=AccountType.PERSONAL)
    active = models.BooleanField(default=True)
    last_modified = models.DateTimeField(auto_now=True)
    show_on_dashboard = models.BooleanField(default=False)
    iban = models.CharField(max_length=34, blank=True, null=True)
    import_ibans = models.TextField(default='[]')
    import_names = models.TextField(default='[]')

    objects = AccountQuerySet.as_manager()

    class Meta:
        ordering = ['-active', 'name']
        unique_together = (('name', 'account_type'),)

    def __str__(self):
        return self.name

    @property
    def account_type_str(self):
        return Account.AccountType.labels[self.account_type - 1]

    @property
    def is_personal(self):
        return self.account_type == Account.AccountType.PERSONAL

    @property
    def transaction_num(self):
        """
        TODO do we really want the number of splits?
        """
        return Split.objects.filter(account=self).count()

    @property
    def balance(self):
        return self.balance_on(date.today())

    def balance_on(self, date):
        return Split.objects.filter(account=self, date__lte=date).aggregate(
            models.Sum('amount'))['amount__sum'] or 0

    def get_absolute_url(self):
        return reverse('account_view', args=[self.pk])

    def get_data_points(self, dstart=date.today() - timedelta(days=365),
                        dend=date.today(), steps=30):
        step = (dend - dstart) / steps
        if step < timedelta(days=1):
            step = timedelta(days=1)
            steps = int((dend - dstart) / step)
        data_points = []
        balance = self.balance_on(dstart - timedelta(days=1))
        transactions = list(Split.objects.prefetch_related('transaction').filter(
            account_id=self.pk).date_range(dstart, dend).order_by(
            '-transaction__date'))
        for i in range(steps):
            while len(transactions) > 0 and transactions[-1].transaction.date <= dstart:
                t = transactions.pop()
                balance += t.amount
            data_points.append((dstart, balance))
            dstart += step
        for t in transactions:
            balance += t.amount
        data_points.append((dend, balance))
        return data_points

    def set_initial_balance(self, amount):
        system = Account.objects.get(account_type=Account.AccountType.SYSTEM)
        transaction = Transaction.objects.create(title=_('Initial Balance'),
                                                 transaction_type=Transaction.SYSTEM,
                                                 src=system,
                                                 dst=self,
                                                 amount=amount)
        Split.objects.create(transaction=transaction, amount=-amount,
                             account=system, opposing_account=self)
        Split.objects.create(transaction=transaction, amount=amount,
                             account=self, opposing_account=system)


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
    src = models.ForeignKey(Account, models.CASCADE, 'debits')
    dst = models.ForeignKey(Account, models.CASCADE, 'credits')
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
        return self.filter(account__account_type=Account.AccountType.PERSONAL)

    def income(self):
        return self.filter(opposing_account__account_type=Account.AccountType.FOREIGN, amount__gt=0)

    def expense(self):
        return self.filter(opposing_account__account_type=Account.AccountType.FOREIGN, amount__lt=0)

    def date_range(self, dstart, dend):
        return self.filter(date__gte=dstart, date__lte=dend)

    def category(self, category):
        return self.filter(category=category)

    def transfers_once(self):
        return self.exclude(
            opposing_account__account_type=Account.AccountType.PERSONAL,
            amount__gte=0)

    def exclude_transfers(self):
        return self.exclude(account__account_type=Account.AccountType.PERSONAL,
                            opposing_account__account_type=Account.AccountType.PERSONAL)

    def upcoming(self):
        return self.filter(date__gt=date.today())

    def past(self):
        return self.filter(date__lte=date.today())

    def recurrence(self, recurrence_id):
        return self.filter(transaction__recurrence_id=recurrence_id)


class Split(models.Model):
    account = models.ForeignKey(Account, models.CASCADE, related_name='incoming_transactions')
    opposing_account = models.ForeignKey(Account, models.CASCADE,
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


class Category(models.Model):
    name = models.CharField(max_length=64)
    active = models.BooleanField(default=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def money_spent(self):
        return abs(Split.objects.filter(
                category=self, account__account_type=Account.AccountType.PERSONAL,
                transaction__transaction_type=Transaction.WITHDRAW).aggregate(
            models.Sum('amount'))['amount__sum'] or 0)

    def get_absolute_url(self):
        return reverse('category_detail', args=[self.id])


class BudgetQuerySet(models.QuerySet):
    def for_month(self, month):
        return self.filter(month=month)


class Budget(models.Model):
    category = models.ForeignKey(Category, models.CASCADE)
    month = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_modified = models.DateTimeField(auto_now=True)

    objects = BudgetQuerySet.as_manager()


class ImportFile(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='imports')
    created_at = models.DateTimeField(auto_now_add=True)
    account = models.ForeignKey(Account, models.SET_NULL, null=True)
    importer = models.PositiveIntegerField(null=True)


class RecurringTransactionManager(models.Manager):
    def due_in_month(self, month=None):
        from .lib import last_day_of_month
        if not month:
            month = date.today()
        month = last_day_of_month(month)
        queryset = self.get_queryset().filter(date__lte=month)
        return queryset.exclude(interval=RecurringTransaction.DISABLED)


class RecurringTransaction(models.Model):
    DISABLED = 0
    MONTHLY = 1
    QUARTERLY = 2
    BIANNUALLY = 3
    ANNUALLY = 4
    WEEKLY = 5
    DAILY = 6

    RECCURENCE_OPTIONS = (
        (DISABLED, _('Disabled')),
        (DAILY, _('Daily')),
        (WEEKLY, _('Weekly')),
        (MONTHLY, _('Monthly')),
        (QUARTERLY, _('Quarterly')),
        (BIANNUALLY, _('Biannually')),
        (ANNUALLY, _('Annually'))
        )

    SAME_DAY = 0
    PREVIOUS_WEEKDAY = 1
    NEXT_WEEKDAY = 2
    SKIP = 3

    WEEKEND_SKIPPING = (
        (SKIP, _('Skip recurrence')),
        (SAME_DAY, _('Same day')),
        (PREVIOUS_WEEKDAY, _('Previous weekday')),
        (NEXT_WEEKDAY, _('Next weekday'))
    )

    class Meta:
        ordering = ['date']

    objects = RecurringTransactionManager()

    title = models.CharField(max_length=64)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    usual_month_day = models.PositiveIntegerField(default=0)
    date = models.DateField()
    src = models.ForeignKey(Account, models.CASCADE)
    dst = models.ForeignKey(Account, models.CASCADE,
                            related_name='opposing_recurring_transactions')
    interval = models.IntegerField(choices=RECCURENCE_OPTIONS)
    transaction_type = models.IntegerField(choices=Transaction.TRANSACTION_TYPES[:3])
    category = models.ForeignKey(Category, models.SET_NULL, null=True, blank=True)
    last_modified = models.DateTimeField(auto_now=True)

    multiplier = models.PositiveIntegerField(default=1)
    weekend_handling = models.IntegerField(default=SAME_DAY, choices=WEEKEND_SKIPPING)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('recurrence_detail', args=[self.pk])

    @property
    def is_due(self):
        return date.today() >= self.date

    def update_date(self, date=None, save=False):
        """
        Calculates the date to the next occurence and optionally saves it.
        It uses the usual_month_day if set for setting the correct day in a monthly recurrence
        """
        delta = None
        if not date:
            date = self.date
        if self.interval == self.MONTHLY:
            delta = relativedelta(months=1)
        elif self.interval == self.QUARTERLY:
            delta = relativedelta(months=3)
        elif self.interval == self.BIANNUALLY:
            delta = relativedelta(months=6)
        elif self.interval == self.ANNUALLY:
            delta = relativedelta(years=1)
        elif self.interval == self.WEEKLY:
            delta = relativedelta(weeks=1)
        elif self.interval == self.DAILY:
            delta = relativedelta(days=1)
        else:
            return
        delta *= self.multiplier
        while True:
            date += delta
            if self.usual_month_day > 0 and self.interval not in [self.WEEKLY, self.DAILY]:
                day = self.usual_month_day
                while True:
                    try:
                        date = date.replace(day=day)
                        break
                    except ValueError:
                        day -= 1
                        pass
            if date.weekday() > 4 and self.interval not in [self.WEEKLY, self.DAILY]:
                if self.weekend_handling == self.SKIP:
                    continue
                elif self.weekend_handling == self.NEXT_WEEKDAY:
                    date += relativedelta(days=7 - date.weekday())
                elif self.weekend_handling == self.PREVIOUS_WEEKDAY:
                    date -= relativedelta(days=date.weekday() - 4)
            if save:
                self.date = date
                self.save()
            return date

    @property
    def is_disabled(self):
        return self.interval == self.DISABLED

    @property
    def get_recurrence(self):
        for r, name in self.RECCURENCE_OPTIONS:
            if r == self.interval:
                return name

    @property
    def signed_amount(self):
        if self.transaction_type == Transaction.WITHDRAW:
            return -self.amount
        else:
            return self.amount

    @property
    def is_withdraw(self):
        return self.transaction_type == Transaction.WITHDRAW

    @property
    def is_deposit(self):
        return self.transaction_type == Transaction.DEPOSIT

    @property
    def average_amount(self):
        return Split.objects.personal().recurrence(self.id).aggregate(
            models.Avg('amount'))['amount__avg']

    @classmethod
    def outstanding_transaction_sum(cls):
        from .lib import last_day_of_month
        outstanding = 0
        dend = last_day_of_month(date.today())
        transactions = cls.objects.due_in_month().exclude(
            transaction_type=Transaction.TRANSFER)
        for t in transactions:
            while t.date <= dend:
                if t.transaction_type == Transaction.WITHDRAW:
                    outstanding -= t.amount
                else:
                    outstanding += t.amount
                t.update_date()
        return outstanding
