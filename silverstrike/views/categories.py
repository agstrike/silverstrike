from collections import defaultdict
from datetime import date

from dateutil.relativedelta import relativedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
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
        categories = defaultdict(int)
        for s in splits:
            categories[s.category] += s.amount
        for c in categories.keys():
            categories[c] = abs(categories[c])
        context['categories'] = dict(categories)
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
        first_day_of_month = date.today().replace(day=1)
        two_months_ago = first_day_of_month - relativedelta(months=2)
        last_month = first_day_of_month - relativedelta(months=1)
        splits = context['category'].splits.filter(account__account_type=Account.PERSONAL,
                                                   date__gte=first_day_of_month)
        last_two_months_splits = context['category'].splits.filter(
            account__account_type=Account.PERSONAL,
            date__gte=two_months_ago, date__lt=first_day_of_month)
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
        splits = splits.select_related('account')
        spent_this_month = 0
        account_spending = defaultdict(int)
        for s in splits:
            spent_this_month += s.amount
            account_spending[s.account] += s.amount

        context['sum_this_month'] = spent_this_month
        context['splits'] = splits
        for account in account_spending.keys():
            account_spending[account] = abs(account_spending[account])
        context['account_spending'] = dict(account_spending)

        return context
