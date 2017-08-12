from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import generic

from pyaccountant.forms import DepositForm, RecurringTransactionForm, TransferForm, WithdrawForm
from pyaccountant.models import RecurringTransaction, TransactionJournal


class RecurrenceCreateView(LoginRequiredMixin, generic.edit.CreateView):
    form_class = RecurringTransactionForm
    model = RecurringTransaction
    success_url = reverse_lazy('recurrences')


class RecurrenceUpdateView(LoginRequiredMixin, generic.edit.UpdateView):
    form_class = RecurringTransactionForm
    model = RecurringTransaction
    success_url = reverse_lazy('recurrences')

    def get_initial(self):
        initial = super().get_initial()
        initial['src'] = self.object.src
        initial['dst'] = self.object.dst
        return initial


class RecurrenceTransactionCreateView(LoginRequiredMixin, generic.edit.CreateView):
    model = TransactionJournal
    template_name = 'pyaccountant/transaction_edit.html'

    def get_form(self, form_class=None):
        self.recurrence = get_object_or_404(RecurringTransaction, pk=self.kwargs['pk'])
        if self.recurrence.transaction_type == TransactionJournal.WITHDRAW:
            form_class = WithdrawForm
        elif self.recurrence.transaction_type == TransactionJournal.DEPOSIT:
            form_class = DepositForm
        else:
            form_class = TransferForm
        return form_class(**self.get_form_kwargs())

    def get_initial(self):
        initial = super().get_initial()
        initial['title'] = self.recurrence.title
        initial['source_account'] = self.recurrence.src
        initial['destination_account'] = self.recurrence.dst
        initial['amount'] = self.recurrence.amount
        initial['date'] = self.recurrence.date
        initial['recurrence'] = self.recurrence.pk
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.recurrence = self.recurrence
        self.object.save()
        self.recurrence.update_date()
        return response

class RecurrenceDeleteView(LoginRequiredMixin, generic.edit.DeleteView):
    model = RecurringTransaction
    success_url = reverse_lazy('recurrences')


class RecurringTransactionIndex(LoginRequiredMixin, generic.ListView):
    template_name = 'pyaccountant/recurring_transactions.html'
    context_object_name = 'transactions'
    model = RecurringTransaction
    paginate_by = 50

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'recurrences'
        return context
