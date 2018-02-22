from datetime import date, datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views import generic

from silverstrike.forms import AccountCreateForm, ReconcilationForm
from silverstrike.models import Account, Split, Transaction


class AccountCreate(LoginRequiredMixin, generic.edit.CreateView):
    model = Account
    form_class = AccountCreateForm
    success_url = reverse_lazy('accounts')

    def get_context_data(self, **kwargs):
        context = super(AccountCreate, self).get_context_data(**kwargs)
        context['menu'] = 'accounts'
        return context


class ForeignAccountCreate(LoginRequiredMixin, generic.edit.CreateView):
    model = Account
    fields = ['name']

    def form_valid(self, form):
        account = form.save(commit=False)
        account.account_type = Account.FOREIGN
        account.save()
        return HttpResponseRedirect(reverse_lazy('foreign_accounts'))


class AccountUpdate(LoginRequiredMixin, generic.edit.UpdateView):
    model = Account
    fields = ['name', 'active', 'show_on_dashboard']

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.account_type == Account.SYSTEM:
            return HttpResponse(_('You are not allowed to edit this account'), status=403)
        return generic.edit.ProcessFormView.post(self, request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.account_type == Account.SYSTEM:
            return HttpResponse(_('You are not allowed to edit this account'), status=403)
        return generic.edit.ProcessFormView.get(self, request, *args, **kwargs)

    def get_form_class(self):
        if self.object.account_type != Account.PERSONAL:
            self.fields = ['name']
        return super(AccountUpdate, self).get_form_class()


class AccountDelete(LoginRequiredMixin, generic.edit.DeleteView):
    model = Account
    success_url = reverse_lazy('accounts')

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.account_type == Account.SYSTEM:
            return HttpResponse(_('You are not allowed to delete this account'), status=403)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.account_type == Account.SYSTEM:
            return HttpResponse(_('You are not allowed to delete this account'), status=403)
        self.object.delete()
        return HttpResponseRedirect(self.success_url)


class AccountIndex(LoginRequiredMixin, generic.TemplateView):
    template_name = 'silverstrike/accounts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'accounts'
        balances = Split.objects.personal().past().order_by('account_id').values(
            'account_id').annotate(Sum('amount'))
        accounts = list(Account.objects.personal().values('id', 'name', 'active'))
        for a in accounts:
            a['balance'] = 0
        for b in balances:
            for a in accounts:
                if a['id'] == b['account_id']:
                    a['balance'] = b['amount__sum']
        context['accounts'] = accounts
        return context


class ForeignAccountIndex(LoginRequiredMixin, generic.ListView):
    template_name = 'silverstrike/foreign_accounts.html'
    queryset = Account.objects.foreign()
    paginate_by = 20


class AccountView(LoginRequiredMixin, generic.ListView):
    template_name = 'silverstrike/account_detail.html'
    context_object_name = 'transactions'
    model = Split

    def dispatch(self, request, *args, **kwargs):
        self.account = Account.objects.get(pk=self.kwargs['pk'])
        if self.account.account_type == Account.SYSTEM:
            return HttpResponse(_('Account not accessible'), status=403)
        if self.kwargs['period'] == 'all':
            self.dstart = None
            self.dend = None
        elif self.kwargs['period'] == 'custom':
            try:
                self.dstart = datetime.strptime(kwargs.pop('dstart'), '%Y-%m-%d').date()
                self.dend = datetime.strptime(kwargs.pop('dend'), '%Y-%m-%d').date()
            except ValueError:
                return HttpResponse(_('Nothing here...'), status=400)
        else:
            self.dend = date.today()
            self.dstart = self.dend - timedelta(days=30)
        return super(AccountView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(account=self.account).select_related(
            'category', 'account', 'transaction', 'opposing_account')
        if self.dstart:
            queryset = queryset.date_range(self.dstart, self.dend)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account'] = self.account
        context['menu'] = 'accounts'

        income = 0
        expenses = 0
        today = date.today()
        if not self.dend:
            for s in context['transactions']:
                self.dend = s.date
                break
        first_date = None
        for s in context['transactions']:
            first_date = s.date
            if s.date > today:
                continue
            if s.amount < 0:
                expenses += s.amount
            elif s.amount > 0:
                income += s.amount
        self.dstart = self.dstart or first_date
        context['dstart'] = self.dstart
        context['dend'] = self.dend
        context['in'] = income
        context['out'] = expenses
        context['difference'] = context['in'] + context['out']
        context['balance'] = self.account.balance
        return context


class ReconcileView(LoginRequiredMixin, generic.edit.CreateView):
    template_name = 'silverstrike/reconcile.html'
    form_class = ReconcilationForm
    model = Transaction

    def dispatch(self, request, *args, **kwargs):
        self.account = Account.objects.get(pk=kwargs['pk'])
        if self.account.account_type != Account.PERSONAL:
            return HttpResponse(_('You can not reconcile this account'), status=403)
        return super(ReconcileView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account'] = self.account
        return context

    def get_form_kwargs(self):
        kwargs = super(ReconcileView, self).get_form_kwargs()
        kwargs['account'] = self.kwargs['pk']
        return kwargs
