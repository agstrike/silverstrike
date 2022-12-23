from datetime import date

from dateutil.relativedelta import relativedelta

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _

from .account import Account
from .category import Category
from .transaction import Split, Transaction
from ..lib import last_day_of_month


class RecurringTransactionManager(models.Manager):
    def due_in_month(self, month=None):
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
        average = Split.objects.personal().recurrence(self.id).aggregate(
            models.Avg('amount'))['amount__avg']
        if not average:
            return '—'
        return round(average, 2)

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
