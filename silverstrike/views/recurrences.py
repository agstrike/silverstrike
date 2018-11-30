from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import generic

from silverstrike.forms import (DepositForm, RecurringDepositForm,
                                RecurringTransactionFormSet, RecurringTransferForm,
                                RecurringWithdrawForm, TransactionFormSet, TransferForm,
                                WithdrawForm)
from silverstrike.lib import last_day_of_month
from silverstrike.models import RecurringSplit, RecurringTransaction, Transaction
from silverstrike.views import transactions


class RecurrenceCreateView(transactions.TransactionCreate):
    model = RecurringTransaction
    template_name = 'silverstrike/recurringtransaction_form.html'

    def get_form_class(self):
        if self.type == 'transfer':
            return RecurringTransferForm
        elif self.type == 'withdraw':
            return RecurringWithdrawForm
        else:
            return RecurringDepositForm


class RecurrenceDetailView(LoginRequiredMixin, generic.DetailView):
    model = RecurringTransaction
    context_object_name = 'recurrence'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'recurrences'
        return context


class RecurrenceUpdateView(LoginRequiredMixin, generic.edit.UpdateView):
    template_name = 'silverstrike/recurringtransaction_form.html'
    model = RecurringTransaction

    def get_initial(self):
        initial = super().get_initial()
        self.recurrence = RecurringSplit.objects.get(
            transaction_id=self.kwargs.get('pk'), amount__gt=0)
        initial['source_account'] = self.recurrence.opposing_account.pk
        initial['destination_account'] = self.recurrence.account.pk
        if self.object.transaction_type == Transaction.WITHDRAW:
            initial['destination_account'] = self.recurrence.account
        elif self.object.transaction_type == Transaction.DEPOSIT:
            initial['source_account'] = self.recurrence.opposing_account
        initial['amount'] = self.recurrence.amount
        initial['category'] = self.recurrence.category
        initial['date'] = self.recurrence.date
        initial['interval'] = self.recurrence.transaction.interval
        initial['multiplier'] = self.recurrence.transaction.multiplier
        return initial

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.exclude(transaction_type=Transaction.SYSTEM)

    def get_form_class(self):
        if self.object.transaction_type == Transaction.WITHDRAW:
            return RecurringWithdrawForm
        elif self.object.transaction_type == Transaction.DEPOSIT:
            return RecurringDepositForm
        else:
            return RecurringTransferForm

    def get_context_data(self, **kwargs):
        context = generic.UpdateView.get_context_data(self, **kwargs)
        context['menu'] = 'recurrences'
        return context


class RecurrenceTransactionCreateView(LoginRequiredMixin, generic.edit.CreateView):
    model = Transaction
    template_name = 'silverstrike/transaction_edit.html'

    def get_form(self, form_class=None):
        self.recurrence = get_object_or_404(RecurringTransaction, pk=self.kwargs['pk'])
        if self.recurrence.transaction_type == Transaction.WITHDRAW:
            form_class = WithdrawForm
        elif self.recurrence.transaction_type == Transaction.DEPOSIT:
            form_class = DepositForm
        else:
            form_class = TransferForm
        return form_class(**self.get_form_kwargs())

    def get_initial(self):
        initial = super().get_initial()
        split = RecurringSplit.objects.get(transaction_id=self.recurrence.pk, amount__gt=0)
        initial['title'] = split.title
        initial['source_account'] = split.opposing_account.pk
        initial['destination_account'] = split.account.pk
        if self.recurrence.transaction_type == Transaction.WITHDRAW:
            initial['destination_account'] = split.account
        elif self.recurrence.transaction_type == Transaction.DEPOSIT:
            initial['source_account'] = split.opposing_account
        initial['amount'] = split.amount
        initial['date'] = split.date
        initial['recurrence'] = self.recurrence.pk
        initial['category'] = split.category
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.recurrence = self.recurrence
        self.object.save()
        self.recurrence.update_date(save=True)
        self.recurrence.save()
        return response


class RecurrenceSplitCreateView(LoginRequiredMixin, generic.edit.CreateView):
    model = Transaction
    template_name = 'silverstrike/transaction_split_form.html'
    formset_class = TransactionFormSet
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        formset_initial = self.recurrence.splits.all().values(
            'title', 'date', 'amount', 'account', 'opposing_account', 'category')
        self.formset_class.extra = len(formset_initial)
        context['formset'] = self.formset_class(initial=formset_initial)
        return context

    def get_initial(self):
        initial = super().get_initial()
        self.recurrence = get_object_or_404(RecurringTransaction, pk=self.kwargs['pk'])
        initial['title'] = self.recurrence.title
        initial['date'] = self.recurrence.date
        initial['recurrence'] = self.recurrence.pk
        initial['transaction_type'] = self.recurrence.transaction_type
        return initial

    def post(self, request, *args, **kwargs):
        form = self.get_form(self.get_form_class())

        if form.is_valid():
            self.recurrence.update_date(save=True)
            self.recurrence.save()
            transaction = form.save(commit=False)
            formset = self.formset_class(self.request.POST, instance=transaction)
            if formset.is_valid():
                transaction.save()
                formset.save()
                return HttpResponseRedirect(reverse('transaction_detail', args=[transaction.id]))
        return self.render_to_response(self.get_context_data(form=form))


class RecurrenceDeleteView(LoginRequiredMixin, generic.edit.DeleteView):
    model = RecurringTransaction
    success_url = reverse_lazy('recurrences')


class RecurringTransactionIndex(LoginRequiredMixin, generic.ListView):
    template_name = 'silverstrike/recurring_transactions.html'
    context_object_name = 'recurrences'
    queryset = RecurringSplit.objects.transfers_once().not_disabled()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'recurrences'
        context['submenu'] = 'all'
        income = 0
        expenses = 0
        first = date.today().replace(day=1)
        last = last_day_of_month(first)
        remaining = 0
        for t in RecurringTransaction.objects.not_disabled().exclude(
                transaction_type=RecurringTransaction.TRANSFER):
            if t.transaction_type == Transaction.WITHDRAW:
                past_expenses = t.sum_amount(first, last)
                future_expenses = t.sum_future_amount(last)
                expenses += past_expenses + future_expenses
                remaining += future_expenses
            else:
                past_income = t.sum_amount(first, last)
                future_income = t.sum_future_amount(last)
                income += past_income + future_income
                remaining += future_income
        context['expenses'] = expenses
        context['income'] = income
        context['total'] = income + expenses
        context['remaining'] = remaining
        return context


class DisabledRecurrencesView(LoginRequiredMixin, generic.ListView):
    template_name = 'silverstrike/disabled_recurrences.html'
    queryset = RecurringTransaction.objects.filter(interval=RecurringTransaction.DISABLED)
    paginate_by = 20


class RecurringSplitCreate(transactions.SplitCreate):
    model = RecurringTransaction
    template_name = 'silverstrike/recurringtransaction_split_form.html'
    formset_class = RecurringTransactionFormSet

    def post(self, request, *args, **kwargs):
        form = self.get_form(self.get_form_class())

        if form.is_valid():
            recurring_transaction = form.save(commit=False)
            formset = self.formset_class(self.request.POST, instance=recurring_transaction)
            if formset.is_valid():
                recurring_transaction.save()
                formset.save()
                return HttpResponseRedirect(
                    reverse(
                        'recurrence_detail', args=[
                            recurring_transaction.id]))
        return self.render_to_response(self.get_context_data(form=form))


class RecurringSplitUpdate(transactions.SplitUpdate):
    model = RecurringTransaction
    template_name = 'silverstrike/recurringtransaction_split_form.html'
    formset_class = RecurringTransactionFormSet

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form(self.get_form_class())

        if form.is_valid():
            recurring_transaction = form.save(commit=False)
            formset = self.formset_class(self.request.POST, instance=recurring_transaction)
            if formset.is_valid():
                fields = [form.cleaned_data.get('amount') for form in formset]
                split_sums = sum([x for x in fields if x is not None])
                if split_sums == 0:
                    recurring_transaction.save()
                    formset.save()
                    return HttpResponseRedirect(reverse('recurrence_detail',
                                                        args=[recurring_transaction.id]))
                else:
                    form.add_error(
                        '',
                        'Sum of all splits has to be 0. You have {} remaining'.format(split_sums))
        return self.render_to_response(self.get_context_data(form=form))
