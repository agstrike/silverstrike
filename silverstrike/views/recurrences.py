from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import generic

from silverstrike.forms import DepositForm, RecurringTransactionForm, TransferForm, WithdrawForm
from silverstrike.models import Journal, RecurringTransaction


class RecurrenceCreateView(LoginRequiredMixin, generic.edit.CreateView):
    form_class = RecurringTransactionForm
    model = RecurringTransaction
    success_url = reverse_lazy('recurrences')


class RecurrenceDetailView(LoginRequiredMixin, generic.DetailView):
    model = RecurringTransaction
    context_object_name = 'recurrence'


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
    model = Journal
    template_name = 'silverstrike/transaction_edit.html'

    def get_form(self, form_class=None):
        self.recurrence = get_object_or_404(RecurringTransaction, pk=self.kwargs['pk'])
        if self.recurrence.transaction_type == Journal.WITHDRAW:
            form_class = WithdrawForm
        elif self.recurrence.transaction_type == Journal.DEPOSIT:
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
        self.recurrence.save()
        return response


class RecurrenceDeleteView(LoginRequiredMixin, generic.edit.DeleteView):
    model = RecurringTransaction
    success_url = reverse_lazy('recurrences')


class RecurringTransactionIndex(LoginRequiredMixin, generic.ListView):
    template_name = 'silverstrike/recurring_transactions.html'
    context_object_name = 'transactions'
    model = RecurringTransaction
    paginate_by = 50

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'recurrences'
        return context
