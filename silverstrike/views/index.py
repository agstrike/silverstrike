from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.views import generic

from rest_framework.authtoken.models import Token as AuthToken

from silverstrike.lib import last_day_of_month
from silverstrike.models import Account, RecurringTransaction, Split, Transaction


class IndexView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'silverstrike/index.html'

    def get_context_data(self, **kwargs):
        dstart = date.today().replace(day=1)
        dend = last_day_of_month(dstart)
        context = super().get_context_data(**kwargs)
        context['menu'] = 'home'
        queryset = Split.objects.personal().past()
        context['balance'] = queryset.aggregate(
            models.Sum('amount'))['amount__sum'] or 0
        queryset = queryset.date_range(dstart, dend)
        context['income'] = abs(queryset.income().aggregate(
                models.Sum('amount'))['amount__sum'] or 0)
        context['expenses'] = abs(queryset.expense().aggregate(
                models.Sum('amount'))['amount__sum'] or 0)
        context['difference'] = context['income'] - context['expenses']

        context['accounts'] = Account.objects.personal().shown_on_dashboard()
        upcoming = Split.objects.personal().upcoming().transfers_once()
        recurrences = RecurringTransaction.objects.due_in_month()

        context['upcoming_transactions'] = upcoming
        context['upcoming_recurrences'] = recurrences
        context['transactions'] = Split.objects.personal().transfers_once().past().select_related(
            'account', 'opposing_account', 'category', 'transaction')[:10]
        outstanding = 0
        for t in upcoming:
            if t.transaction.transaction_type != Transaction.TRANSFER:
                outstanding += t.amount
        context['working_balance'] = context['balance'] + outstanding
        outstanding = 0
        for r in recurrences:
            if r.transaction_type == Transaction.WITHDRAW:
                outstanding -= r.amount
            elif r.transaction_type == Transaction.DEPOSIT:
                outstanding += r.amount
            if r.is_due:
                context['overdue_transactions'] = True

        context['outstanding'] = outstanding
        context['expected_balance'] = context['working_balance'] + outstanding

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
        context['last_month'] = previous_first
        context['past'] = date.today() - timedelta(days=60)
        return context


class ProfileView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'silverstrike/profile.html'

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data()
        context['token'], created = AuthToken.objects.get_or_create(user=self.request.user)
        return context
