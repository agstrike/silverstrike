import csv
import os

from datetime import date, datetime, timedelta

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views import generic

from .forms import DepositForm, ImportUploadForm, TransferForm, WithdrawForm
from .lib import last_day_of_month
from .models import Account, Category, ImportConfiguration, ImportFile, Transaction, TransactionJournal


class AccountCreate(LoginRequiredMixin, generic.edit.CreateView):
    model = Account
    fields = ['name', 'active']
    success_url = reverse_lazy('personal_accounts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'accounts'
        context['submenu'] = 'new'
        return context


class AccountUpdate(LoginRequiredMixin, generic.edit.UpdateView):
    model = Account
    fields = ['name', 'active']


class AccountDelete(LoginRequiredMixin, generic.edit.DeleteView):
    model = Account
    success_url = reverse_lazy('personal_accounts')


class AccountIndex(LoginRequiredMixin, generic.ListView):
    template_name = 'pyaccountant/accounts.html'
    context_object_name = 'accounts'
    account_type = ''

    def get_queryset(self):
        return Account.objects.filter(internal_type=self.account_type)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'accounts'
        if self.account_type == Account.PERSONAL:
            context['submenu'] = 'personal'
        elif self.account_type == Account.EXPENSE:
            context['submenu'] = 'expense'
        else:
            context['submenu'] = 'revenue'
        return context


class CategoryIndex(LoginRequiredMixin, generic.ListView):
    template_name = 'pyaccountant/category_index.html'
    context_object_name = 'categories'
    model = Category

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'categories'
        return context


class TransactionIndex(LoginRequiredMixin, generic.ListView):
    template_name = 'pyaccountant/transaction_overview.html'
    context_object_name = 'transactions'
    model = Transaction
    paginate_by = 50
    ordering = ['-journal__date']

    def get_queryset(self):
        queryset = super().get_queryset().filter(account__internal_type=Account.PERSONAL)
        if 'category' in self.request.GET:
            queryset = queryset.filter(journal__category_id=self.request.GET['category'])
        if 'account' in self.request.GET:
            queryset = queryset.filter(account_id=self.request.GET['account'])
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'transactions'
        context['submenu'] = 'all'
        return context


class AccountView(LoginRequiredMixin, generic.ListView):
    template_name = 'pyaccountant/account_detail.html'
    context_object_name = 'transactions'
    model = Transaction
    paginate_by = 50
    ordering = ['-journal__date']

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(account=self.kwargs.get('pk')).select_related(
            'journal__category', 'account')
        self.dstart = datetime.strptime(self.kwargs.get('dstart'), '%Y-%m-%d')

        queryset = queryset.filter(journal__date__gte=self.dstart)
        self.dend = last_day_of_month(self.dstart)
        queryset = queryset.filter(journal__date__lte=self.dend)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'accounts'
        context['submenu'] = 'personal'
        context['dstart'] = self.dstart

        context['previous_month'] = (self.dstart - timedelta(days=1)).replace(day=1)
        context['next_month'] = self.dend + timedelta(days=1)
        context['account'] = Account.objects.get(pk=self.kwargs['pk'])
        context.update(_get_account_info(self.dstart, self.dend, context['account']))

        delta = timedelta(days=3)
        if context['account'].internal_type == Account.PERSONAL:
            context['dataset'] = context['account'].get_data_points(
                self.dstart - delta, self.dend + delta)
        return context


class TransferCreate(LoginRequiredMixin, generic.edit.CreateView):
    model = TransactionJournal
    form_class = TransferForm
    template_name = 'pyaccountant/transaction_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'transactions'
        context['submenu'] = 'transfer'
        return context


class TransferUpdate(LoginRequiredMixin, generic.edit.UpdateView):
    template_name = 'pyaccountant/transaction_edit.html'
    model = TransactionJournal

    def get_initial(self):
        initial = super().get_initial()
        self.transaction = Transaction.objects.get(journal_id=self.kwargs.get('pk'), amount__gt=0)
        initial['source_account'] = self.transaction.opposing_account.pk
        initial['destination_account'] = self.transaction.account.pk
        if self.object.transaction_type == TransactionJournal.WITHDRAW:
            initial['destination_account'] = self.transaction.account
        elif self.object.transaction_type == TransactionJournal.DEPOSIT:
            initial['source_account'] = self.transaction.opposing_account
        initial['amount'] = self.transaction.amount
        return initial

    def get_form_class(self):
        if self.object.transaction_type == TransactionJournal.WITHDRAW:
            return WithdrawForm
        elif self.object.transaction_type == TransactionJournal.DEPOSIT:
            return DepositForm
        else:
            return TransferForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'transactions'
        return context


class WithdrawCreate(TransferCreate):
    form_class = WithdrawForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submenu'] = 'withdraw'
        return context


class DepositCreate(TransferCreate):
    form_class = DepositForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['submenu'] = 'deposit'
        return context


def _get_account_info(dstart, dend, account=None):
    context = dict()
    queryset = Transaction.objects.filter(
        journal__date__gte=dstart,
        journal__date__lte=dend)
    if account:
        queryset = queryset.filter(account=account)
    context['income'] = abs(queryset.filter(
        account__internal_type=Account.PERSONAL,
        opposing_account__internal_type=Account.REVENUE).aggregate(
            models.Sum('amount'))['amount__sum'] or 0)

    context['expenses'] = abs(queryset.filter(
        account__internal_type=Account.PERSONAL,
        opposing_account__internal_type=Account.EXPENSE).aggregate(
            models.Sum('amount'))['amount__sum'] or 0)
    context['difference'] = context['income'] - context['expenses']
    return context


class IndexView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'pyaccountant/index.html'

    def get_context_data(self, **kwargs):
        first = date.today().replace(day=1)
        last = last_day_of_month(first)
        context = super().get_context_data(**kwargs)
        context['menu'] = 'home'
        queryset = Transaction.objects.filter(account__internal_type=Account.PERSONAL)
        context['balance'] = queryset.aggregate(
            models.Sum('amount'))['amount__sum'] or 0
        context.update(_get_account_info(first, last))
        context['accounts'] = Account.objects.filter(internal_type=Account.PERSONAL)
        return context


class ImportUploadView(LoginRequiredMixin, generic.edit.CreateView):
    template_name = 'pyaccountant/import.html'
    model = ImportFile
    form_class = ImportUploadForm

    def form_valid(self, form):
        self.configuration = form.cleaned_data['configuration']
        return super().form_valid(form)

    def get_success_url(self):
        if self.configuration:
            return reverse('import_process', args=[self.object.pk, self.configuration.pk])
        else:
            return reverse('import_configure', args=(self.object.pk,))


class ImportConfigureView(LoginRequiredMixin, generic.CreateView):
    model = ImportConfiguration
    template_name = 'pyaccountant/import_configure.html.j2'
    fields = ['name', 'headers']

    def get_success_url(self):
        return reverse('import_process', args=[self.kwargs['pk'], self.object.pk])


class ImportProcessView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'pyaccountant/import_process.html.j2'


class ChartView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'pyaccountant/charts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'charts'
        context['today'] = date.today()
        currentMonth = date.today().month
        currentYear = date.today().year
        minus_3_m = currentMonth - 3
        minus_3_y = currentYear
        if minus_3_m < 1:
            minus_3_m += 12
            minus_3_y -= 1
        minus_6_m = currentMonth - 6
        minus_6_y = currentYear
        if minus_6_m < 1:
            minus_6_m += 12
            minus_6_y -= 1
        context['minus_3_months'] = date.today().replace(month=minus_3_m, year=minus_3_y)
        context['minus_6_months'] = date.today().replace(month=minus_6_m, year=minus_6_y)
        context['minus_12_months'] = date.today().replace(year=currentYear - 1)

        context['first_day_of_month'] = date.today().replace(day=1)
        context['last_day_of_month'] = last_day_of_month(date.today())
        return context
