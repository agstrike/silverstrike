from collections import defaultdict
from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views import generic

from silverstrike.models import Account, Category


class CategoryIndex(LoginRequiredMixin, generic.ListView):
    template_name = 'silverstrike/category_index.html'
    context_object_name = 'categories'
    model = Category

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'categories'
        return context


class CategoryCreateView(LoginRequiredMixin, generic.edit.CreateView):
    model = Category
    fields = ['name']
    success_url = reverse_lazy('categories')


class CategoryUpdateView(LoginRequiredMixin, generic.edit.UpdateView):
    pass


class CategroyDeleteView(LoginRequiredMixin, generic.edit.DeleteView):
    pass


class CategoryDetailView(LoginRequiredMixin, generic.DetailView):
    model = Category
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super(CategoryDetailView, self).get_context_data(**kwargs)
        splits = context['category'].splits.filter(account__account_type=Account.PERSONAL,
                                                   date__gte=date.today().replace(day=1))
        splits = splits.select_related('account')
        spent_this_month = 0
        account_spending = defaultdict(int)
        for s in splits:
            spent_this_month += s.amount
            account_spending[s.account] += s.amount

        context['spent_this_month'] = abs(spent_this_month)
        context['splits'] = splits
        for account in account_spending.keys():
            account_spending[account] = abs(account_spending[account])
        context['account_spending'] = dict(account_spending)

        return context
