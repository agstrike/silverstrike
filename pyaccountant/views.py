from django.urls import reverse_lazy
from django.views import generic

from .forms import DepositForm, TransferForm, WithdrawForm
from .models import Account, Category, Transaction, TransactionJournal


class AccountCreate(generic.edit.CreateView):
    model = Account
    fields = ['name', 'account_type', 'active']
    success_url = reverse_lazy('personal_accounts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'accounts'
        context['submenu'] = 'new'
        return context


class AccountUpdate(generic.edit.UpdateView):
    model = Account
    fields = ['name', 'account_type', 'active']


class AccountDelete(generic.edit.DeleteView):
    model = Account
    success_url = reverse_lazy('personal_accounts')


class AccountIndex(generic.ListView):
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


class CategoryIndex(generic.ListView):
    template_name = 'pyaccountant/category_index.html'
    context_object_name = 'categories'
    model = Category
    ordering = ['group']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'categories'
        return context


class TransactionIndex(generic.ListView):
    template_name = 'pyaccountant/transaction_overview.html'
    context_object_name = 'transactions'
    model = Transaction
    paginate_by = 50
    ordering = ['-journal__date']

    def get_queryset(self):
        queryset = super().get_queryset()
        if 'pk' in self.kwargs:
            return queryset.filter(account=self.kwargs.get('pk'))
        return queryset.filter(account__internal_type=Account.PERSONAL)

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


class TransferUpdate(generic.edit.UpdateView):
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


class IndexView(generic.TemplateView):
    template_name = 'pyaccountant/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'home'
        return context
