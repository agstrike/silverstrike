from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views import generic

from silverstrike.forms import DepositForm, ReconcilationForm, TransferForm, WithdrawForm
from silverstrike.models import Account, Transaction, TransactionJournal


class TransactionDetailView(LoginRequiredMixin, generic.DetailView):
    model = Transaction
    context_object_name = 'transaction'

    def get_object(self, queryset=None):
        queryset = Transaction.objects.all()
        queryset = queryset.select_related('journal', 'journal__category',
                                           'account', 'opposing_account')
        transaction = queryset.get(journal_id=self.kwargs['pk'], amount__lt=0)
        if transaction.journal.transaction_type != TransactionJournal.WITHDRAW:
            transaction.amount = -transaction.amount
        return transaction


class TransactionDeleteView(LoginRequiredMixin, generic.edit.DeleteView):
    model = TransactionJournal
    success_url = reverse_lazy('personal_accounts')


class TransactionIndex(LoginRequiredMixin, generic.ListView):
    template_name = 'silverstrike/transaction_overview.html'
    context_object_name = 'transactions'
    model = Transaction
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset().filter(account__account_type=Account.PERSONAL)
        queryset = queryset.exclude(journal__transaction_type=TransactionJournal.TRANSFER,
                                    amount__gt=0)
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


class TransferCreate(LoginRequiredMixin, generic.edit.CreateView):
    model = TransactionJournal
    form_class = TransferForm
    template_name = 'silverstrike/transaction_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'transactions'
        context['submenu'] = 'transfer'
        return context


class TransactionUpdateView(LoginRequiredMixin, generic.edit.UpdateView):
    template_name = 'silverstrike/transaction_edit.html'
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


class ReconcileView(LoginRequiredMixin, generic.edit.CreateView):
    template_name = 'silverstrike/reconcile.html'
    form_class = ReconcilationForm
    model = TransactionJournal

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account'] = Account.objects.get(pk=self.kwargs['pk'])
        return context

    def get_form_kwargs(self):
        kwargs = super(ReconcileView, self).get_form_kwargs()
        kwargs['account'] = self.kwargs['pk']
        return kwargs
