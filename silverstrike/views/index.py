from datetime import date, datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.views import generic

from silverstrike.models import Account, RecurringTransaction, Split


def _get_account_info(dstart, dend):
    context = dict()
    queryset = Split.objects.filter(
        date__gte=dstart,
        date__lte=dend)
    context['income'] = abs(queryset.filter(
        account__account_type=Account.PERSONAL,
        opposing_account__account_type=Account.REVENUE).aggregate(
            models.Sum('amount'))['amount__sum'] or 0)

    context['expenses'] = abs(queryset.filter(
        account__account_type=Account.PERSONAL,
        opposing_account__account_type=Account.EXPENSE).aggregate(
            models.Sum('amount'))['amount__sum'] or 0)
    context['difference'] = context['income'] - context['expenses']
    return context


class IndexView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'silverstrike/index.html'

    def get_context_data(self, **kwargs):
        first = date.today().replace(day=1)
        context = super().get_context_data(**kwargs)
        context['menu'] = 'home'
        queryset = Split.objects.filter(account__account_type=Account.PERSONAL)
        context['balance'] = queryset.aggregate(
            models.Sum('amount'))['amount__sum'] or 0

        context['income'] = Split.objects.income(month=first)
        context['expenses'] = abs(Split.objects.expenses(month=first))
        context['difference'] = context['income'] - context['expenses']

        context['accounts'] = Account.objects.filter(account_type=Account.PERSONAL,
                                                     show_on_dashboard=True)
        context['due_transactions'] = RecurringTransaction.objects.due_in_month()
        context['transactions'] = Split.objects.filter(
            account__account_type=Account.PERSONAL)[:10]
        context['outstanding'] = RecurringTransaction.outstanding_transaction_sum()
        context['expected_balance'] = context['balance'] + context['outstanding']

        # last month
        previous_last = first - timedelta(days=1)
        previous_first = previous_last.replace(day=1)
        queryset = Split.objects.filter(date__lte=previous_last,
                                        date__gte=previous_first)
        context['previous_income'] = abs(queryset.filter(
            account__account_type=Account.PERSONAL,
            opposing_account__account_type=Account.REVENUE).aggregate(
            models.Sum('amount'))['amount__sum'] or 0)

        context['previous_expenses'] = abs(queryset.filter(
            account__account_type=Account.PERSONAL,
            opposing_account__account_type=Account.EXPENSE).aggregate(
                models.Sum('amount'))['amount__sum'] or 0)
        context['previous_difference'] = context['previous_income'] - context['previous_expenses']
        context['today'] = datetime.strftime(date.today(), '%Y-%m-%d')
        context['past'] = datetime.strftime(date.today() - timedelta(days=60), '%Y-%m-%d')
        return context
