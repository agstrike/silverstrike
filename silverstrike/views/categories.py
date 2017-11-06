from collections import defaultdict
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views import generic

from silverstrike.lib import last_day_of_month
from silverstrike.models import Account, Category, Split


class CategoryIndex(LoginRequiredMixin, generic.TemplateView):
    template_name = 'silverstrike/category_index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'categories'
        dstart = date.today().replace(day=1)
        dend = last_day_of_month(dstart)

        splits = Split.objects.personal().date_range(dstart, dend).select_related('category')
        categories = {c: 0 for c in Category.objects.all()}
        for s in splits:
            categories[s.category] += s.amount
        for c in categories.keys():
            categories[c] = abs(categories[c])
        context['categories'] = categories
        return context


class CategoryCreateView(LoginRequiredMixin, generic.edit.CreateView):
    model = Category
    fields = ['name']
    success_url = reverse_lazy('categories')


class CategoryUpdateView(LoginRequiredMixin, generic.edit.UpdateView):
    model = Category
    fields = ['name']

    def get_success_url(self):
        return reverse('category_detail', args=[self.object.id])


class CategoryDeleteView(LoginRequiredMixin, generic.edit.DeleteView):
    model = Category
    success_url = reverse_lazy('categories')


class CategoryDetailView(LoginRequiredMixin, generic.DetailView):
    model = Category
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super(CategoryDetailView, self).get_context_data(**kwargs)

        if 'month' in self.kwargs:
            current_month = datetime.strptime(self.kwargs.get('month'), '%Y%m').date()
        else:
            current_month = date.today().replace(day=1)

        next_month = current_month + relativedelta(months=1)
        two_months_ago = current_month - relativedelta(months=2)
        last_month = current_month - relativedelta(months=1)
        splits = context['category'].splits.filter(account__account_type=Account.PERSONAL,
                                                   date__gte=current_month, date__lt=next_month)
        last_two_months_splits = context['category'].splits.filter(
            account__account_type=Account.PERSONAL,
            date__gte=two_months_ago, date__lt=current_month)
        sum_last_month = 0
        sum_two_months_ago = 0
        for s in last_two_months_splits:
            if s.date < last_month:
                sum_two_months_ago += s.amount
            else:
                sum_last_month += s.amount
        context['sum_two_months_ago'] = sum_two_months_ago
        context['sum_last_month'] = sum_last_month
        context['average'] = (sum_last_month + sum_two_months_ago) / 2
        splits = splits.select_related('account', 'opposing_account')
        spent_this_month = 0
        account_spending = defaultdict(int)
        destination_spending = defaultdict(int)
        for s in splits:
            spent_this_month += s.amount
            account_spending[s.account] += s.amount
            destination_spending[s.opposing_account] += s.amount

        context['sum_this_month'] = spent_this_month
        context['splits'] = splits
        for account in account_spending.keys():
            account_spending[account] = abs(account_spending[account])

        for account in destination_spending.keys():
            destination_spending[account] = abs(destination_spending[account])
        context['account_spending'] = dict(account_spending)
        context['destination_spending'] = dict(destination_spending)

        context['current_month'] = current_month
        context['previous_month'] = last_month
        context['next_month'] = current_month + relativedelta(months=1)
        context['month_before'] = two_months_ago

        return context
