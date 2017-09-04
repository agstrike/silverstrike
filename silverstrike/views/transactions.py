from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views import generic

from silverstrike.forms import DepositForm, TransactionFormSet, TransferForm, WithdrawForm
from silverstrike.models import Account, Journal, Split


class TransactionDetailView(LoginRequiredMixin, generic.DetailView):
    model = Journal
    context_object_name = 'journal'


class TransactionDeleteView(LoginRequiredMixin, generic.edit.DeleteView):
    model = Journal
    success_url = reverse_lazy('personal_accounts')


class TransactionIndex(LoginRequiredMixin, generic.ListView):
    template_name = 'silverstrike/transaction_overview.html'
    context_object_name = 'transactions'
    model = Split
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset().filter(account__account_type=Account.PERSONAL)

        if 'category' in self.request.GET:
            queryset = queryset.filter(category_id=self.request.GET['category'])
        if 'account' in self.request.GET:
            queryset = queryset.filter(account_id=self.request.GET['account'])
        else:
            queryset = queryset.exclude(journal__transaction_type=Journal.TRANSFER,
                                        amount__gt=0)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'transactions'
        context['submenu'] = 'all'
        return context


class TransferCreate(LoginRequiredMixin, generic.edit.CreateView):
    model = Journal
    form_class = TransferForm
    template_name = 'silverstrike/transaction_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'transactions'
        context['submenu'] = 'transfer'
        return context


class TransactionUpdateView(LoginRequiredMixin, generic.edit.UpdateView):
    template_name = 'silverstrike/transaction_edit.html'
    model = Journal

    def get_initial(self):
        initial = super().get_initial()
        self.transaction = Split.objects.get(journal_id=self.kwargs.get('pk'), amount__gt=0)
        initial['source_account'] = self.transaction.opposing_account.pk
        initial['destination_account'] = self.transaction.account.pk
        if self.object.transaction_type == Journal.WITHDRAW:
            initial['destination_account'] = self.transaction.account
        elif self.object.transaction_type == Journal.DEPOSIT:
            initial['source_account'] = self.transaction.opposing_account
        initial['amount'] = self.transaction.amount
        return initial

    def get_form_class(self):
        if self.object.transaction_type == Journal.WITHDRAW:
            return WithdrawForm
        elif self.object.transaction_type == Journal.DEPOSIT:
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


class NewTransactionView(generic.edit.CreateView):
    model = Journal
    template_name = 'silverstrike/newform.html'
    formset_class = TransactionFormSet
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super(NewTransactionView, self).get_context_data(**kwargs)
        context['formset'] = self.formset_class()
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form(self.get_form_class())

        if form.is_valid():
            journal = form.save(commit=False)
            formset = self.formset_class(self.request.POST, instance=journal)
            if formset.is_valid():
                journal.save()
                formset.save()
                return HttpResponseRedirect('/')
        return self.render_to_response(self.get_context_data(form=form))


class EditTransactionView(generic.edit.UpdateView):
    model = Journal
    template_name = 'silverstrike/newform.html'
    formset_class = TransactionFormSet
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super(NewTransactionView, self).get_context_data(**kwargs)
        context['formset'] = self.formset_class()
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form(self.get_form_class())

        if form.is_valid():
            journal = form.save(commit=False)
            formset = self.formset_class(self.request.POST, instance=journal)
            if formset.is_valid():
                journal.save()
                formset.save()
                return HttpResponseRedirect('/')
        return self.render_to_response(self.get_context_data(form=form))
