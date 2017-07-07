from django import http
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

from .forms import DepositForm, TransferForm, WithdrawForm
from .models import Account, InternalAccountType, Transaction, TransactionJournal


class AccountCreate(generic.edit.CreateView):
    model = Account
    fields = ['name', 'currency', 'account_type', 'active']
    success_url = reverse_lazy('personal_accounts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'accounts'
        context['submenu'] = 'new'
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.internal_type = InternalAccountType.personal.value
        self.object.save()
        return http.HttpResponseRedirect(self.get_success_url())


class AccountUpdate(generic.edit.UpdateView):
    model = Account
    fields = ['name', 'currency', 'account_type', 'active']


class AccountDelete(generic.edit.DeleteView):
    model = Account
    success_url = reverse_lazy('personal_accounts')


class ExpenseAccountIndex(generic.ListView):
    template_name = 'pyaccountant/accounts.html'
    context_object_name = 'accounts'

    def get_queryset(self):
        return Account.objects.filter(internal_type=InternalAccountType.expense.value)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'accounts'
        context['submenu'] = 'expense'
        return context


class PersonalAccountIndex(generic.ListView):
    template_name = 'pyaccountant/accounts.html'
    context_object_name = 'accounts'

    def get_queryset(self):
        return Account.objects.filter(internal_type=InternalAccountType.personal.value)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'accounts'
        context['submenu'] = 'personal'
        return context


class RevenueAccountIndex(generic.ListView):
    template_name = 'pyaccountant/accounts.html'
    context_object_name = 'accounts'

    def get_queryset(self):
        return Account.objects.filter(internal_type=InternalAccountType.revenue.value)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'accounts'
        context['submenu'] = 'revenue'
        return context


class TransactionIndex(generic.ListView):
    template_name = 'pyaccountant/transaction_overview.html'
    context_object_name = 'transactions'

    def get_queryset(self):
        if 'pk' in self.kwargs:
            return Transaction.objects.filter(account=self.kwargs.get('pk'))
        return Transaction.objects.filter(account__internal_type=InternalAccountType.personal.value)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'transactions'
        context['submenu'] = 'all'
        if 'pk' in self.kwargs:
            context['account'] = Account.objects.get(pk=self.kwargs['pk'])
        return context


class TransferCreate(generic.edit.CreateView):
    model = TransactionJournal
    form_class = TransferForm
    template_name = 'pyaccountant/transaction_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'transactions'
        context['submenu'] = 'transfer'
        return context


class TransactionUpdate(generic.edit.UpdateView):
    template_name = 'pyaccountant/transaction_edit.html'
    form_class = TransferForm
    model = TransactionJournal

    def get_initial(self):
        initial = super().get_initial()
        transactions = Transaction.objects.filter(journal_id=self.kwargs.get('pk'))
        initial['source_account'] = transactions.get(amount__lt=0).account.pk
        initial['destination_account'] = transactions.get(amount__gt=0).account.pk
        initial['amount'] = transactions.get(amount__gt=0).amount
        return initial

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


def index(request):
    return render(request, 'pyaccountant/index.html', {'menu': 'home'})
