from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.views import generic

from silverstrike.lib import last_day_of_month
from silverstrike.models import Account, RecurringTransaction, Split, Transaction


class IndexView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'silverstrike/index.html'

    def get_context_data(self, **kwargs):
        dstart = date.today().replace(day=1)
        dend = last_day_of_month(dstart)
        context = super().get_context_data(**kwargs)
        context['menu'] = 'home'
        queryset = Split.objects.personal()
        context['balance'] = queryset.aggregate(
            models.Sum('amount'))['amount__sum'] or 0
        queryset = queryset.date_range(dstart, dend)
        context['income'] = abs(queryset.income().past().aggregate(
                models.Sum('amount'))['amount__sum'] or 0)
        context['expenses'] = abs(queryset.expense().past().aggregate(
                models.Sum('amount'))['amount__sum'] or 0)
        context['difference'] = context['income'] - context['expenses']

        context['accounts'] = Account.objects.filter(account_type=Account.PERSONAL,
                                                     show_on_dashboard=True)
        upcoming = Split.objects.personal().upcoming()
        recurrences = RecurringTransaction.objects.due_in_month()

        context['upcoming_transactions'] = upcoming
        context['upcoming_recurrences'] = recurrences
        context['transactions'] = Split.objects.personal().transfers_once().past().select_related(
            'account', 'opposing_account', 'category', 'transaction')[:10]
        outstanding = 0
        for t in upcoming:
            outstanding += t.amount
        for r in recurrences:
            if r.transaction_type == Transaction.WITHDRAW:
                outstanding -= r.amount
            elif r.transaction_type == Transaction.DEPOSIT:
                outstanding += r.amount

        context['outstanding'] = outstanding
        context['expected_balance'] = context['balance'] + outstanding

        # last month
        previous_last = dstart - timedelta(days=1)
        previous_first = previous_last.replace(day=1)
        queryset = Split.objects.personal().date_range(previous_first, previous_last)
        context['previous_income'] = abs(queryset.income().aggregate(
            models.Sum('amount'))['amount__sum'] or 0)

        context['previous_expenses'] = abs(queryset.expense().aggregate(
                models.Sum('amount'))['amount__sum'] or 0)
        context['previous_difference'] = context['previous_income'] - context['previous_expenses']
        context['today'] = date.today()
        context['past'] = date.today() - timedelta(days=60)
        return context
