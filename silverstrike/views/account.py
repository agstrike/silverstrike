from datetime import datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.http import Http404
from django.urls import reverse_lazy
from django.views import generic

from silverstrike.forms import AccountCreateForm, ReconcilationForm
from silverstrike.lib import last_day_of_month
from silverstrike.models import Account, Transaction, TransactionJournal


def _get_account_info(dstart, dend, account=None):
    context = dict()
    queryset = Transaction.objects.filter(
        journal__date__gte=dstart,
        journal__date__lte=dend)
    if account:
        queryset = queryset.filter(account=account)
    context['income'] = abs(queryset.filter(
        journal__transaction_type=TransactionJournal.DEPOSIT).aggregate(
            models.Sum('amount'))['amount__sum'] or 0)

    context['expenses'] = abs(queryset.filter(
        journal__transaction_type=TransactionJournal.WITHDRAW).aggregate(
            models.Sum('amount'))['amount__sum'] or 0)
    context['difference'] = context['income'] - context['expenses']
    return context


class AccountCreate(LoginRequiredMixin, generic.edit.CreateView):
    model = Account
    form_class = AccountCreateForm
    success_url = reverse_lazy('personal_accounts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'accounts'
        context['submenu'] = 'new'
        return context


class AccountUpdate(LoginRequiredMixin, generic.edit.UpdateView):
    model = Account
    fields = ['name', 'active', 'show_on_dashboard']

    def get_form_class(self):
        if self.object.account_type == Account.SYSTEM:
            raise Http404("You aren't allowed to edit this account")
        if self.object.account_type != Account.PERSONAL:
            self.fields = ['name']
        return super(AccountUpdate, self).get_form_class()


class AccountDelete(LoginRequiredMixin, generic.edit.DeleteView):
    model = Account
    success_url = reverse_lazy('personal_accounts')


class AccountIndex(LoginRequiredMixin, generic.ListView):
    template_name = 'silverstrike/accounts.html'
    context_object_name = 'accounts'
    account_type = ''

    def get_queryset(self):
        return Account.objects.filter(account_type=Account.PERSONAL)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'accounts'
        context['submenu'] = 'personal'
        return context


class AccountView(LoginRequiredMixin, generic.ListView):
    template_name = 'silverstrike/account_detail.html'
    context_object_name = 'transactions'
    model = Transaction
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(account=self.kwargs.get('pk')).select_related(
            'journal__category', 'account')
        self.month = datetime.strptime(self.kwargs.get('month'), '%Y%m')

        queryset = queryset.filter(journal__date__gte=self.month)
        self.dend = last_day_of_month(self.month)
        queryset = queryset.filter(journal__date__lte=self.dend)
        return queryset

    def get_context_data(self, **kwargs):
        account = Account.objects.get(pk=self.kwargs['pk'])
        if account.account_type == Account.SYSTEM:
            raise Http404('Account not accessible')
        context = super().get_context_data(**kwargs)
        context['account'] = account
        context['menu'] = 'accounts'
        context['submenu'] = 'personal'
        context['month'] = self.month

        context['previous_month'] = (self.month - timedelta(days=1)).replace(day=1)
        context['next_month'] = self.dend + timedelta(days=1)
        context.update(_get_account_info(self.month, self.dend, account))

        delta = timedelta(days=3)
        if account.account_type == Account.PERSONAL:
            context['dataset'] = account.get_data_points(
                self.month - delta, self.dend + delta)
        context['balance'] = account.balance
        return context


class ReconcileView(LoginRequiredMixin, generic.edit.CreateView):
    template_name = 'silverstrike/reconcile.html'
    form_class = ReconcilationForm
    model = TransactionJournal

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account'] = Account.objects.get(pk=self.kwargs['pk'])
        if context['account'].account_type != Account.PERSONAL:
            raise Http404("You can't reconcile this account")
        return context

    def get_form_kwargs(self):
        kwargs = super(ReconcileView, self).get_form_kwargs()
        kwargs['account'] = self.kwargs['pk']
        return kwargs
