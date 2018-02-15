from collections import defaultdict
from datetime import date

from dateutil.relativedelta import relativedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import generic

from silverstrike.forms import CategoryAssignFormset
from silverstrike.lib import last_day_of_month
from silverstrike.models import Account, Category, Split


class CategoryIndex(LoginRequiredMixin, generic.TemplateView):
    template_name = 'silverstrike/category_index.html'

    def dispatch(self, request, *args, **kwargs):
        if 'month' in kwargs:
            self.month = date(kwargs.pop('year'), kwargs.pop('month'), 1)
        else:
            self.month = date.today().replace(day=1)
        return super(CategoryIndex, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'categories'
        dstart = self.month
        dend = last_day_of_month(dstart)

        categories = Split.objects.personal().past().date_range(dstart, dend).order_by(
            'category').values('category', 'category__name').annotate(spent=Sum('amount'))

        categories = [(e['category'], e['category__name'], abs(e['spent'])) for e in categories]

        all_categories = list(Category.objects.exclude(active=False).values_list('id', 'name'))
        for id, name, spent in categories:
            if id:
                all_categories.remove((id, name))
        for id, name in all_categories:
            categories.append((id, name, 0))
        context['categories'] = categories
        context['month'] = self.month
        context['next_month'] = self.month + relativedelta(months=1)
        context['previous_month'] = self.month - relativedelta(months=1)
        return context


class CategoryCreateView(LoginRequiredMixin, generic.edit.CreateView):
    model = Category
    fields = ['name', 'active']
    success_url = reverse_lazy('categories')


class CategoryUpdateView(LoginRequiredMixin, generic.edit.UpdateView):
    model = Category
    fields = ['name', 'active']

    def get_success_url(self):
        return reverse('category_detail', args=[self.object.id])


class CategoryDeleteView(LoginRequiredMixin, generic.edit.DeleteView):
    model = Category
    success_url = reverse_lazy('categories')


class InactiveCategoriesView(LoginRequiredMixin, generic.ListView):
    model = Category
    template_name = 'silverstrike/inactive_categories.html'

    def get_queryset(self):
        return super(InactiveCategoriesView, self).get_queryset().filter(active=False)


def assign_categories(request):
    queryset = Split.objects.expense().filter(category=None)
    formset = CategoryAssignFormset(queryset=queryset)
    if request.method == 'POST':
        formset = CategoryAssignFormset(request.POST)
        if formset.is_valid():
            for f in formset:
                if f.has_changed():
                    f.save()
            return redirect('category_assign')
    results = zip(queryset, formset.forms)
    return render(request, 'silverstrike/category_assign.html',
                  {'formset': formset, 'results': results})


class CategoryDetailView(LoginRequiredMixin, generic.DetailView):
    model = Category
    context_object_name = 'category'

    def dispatch(self, request, *args, **kwargs):
        if 'month' in kwargs:
            self.current_month = date(kwargs.pop('year'), kwargs.pop('month'), 1)
        else:
            self.current_month = date.today().replace(day=1)
        return super(CategoryDetailView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CategoryDetailView, self).get_context_data(**kwargs)
        next_month = self.current_month + relativedelta(months=1)
        two_months_ago = self.current_month - relativedelta(months=2)
        last_month = self.current_month - relativedelta(months=1)
        splits = context['category'].splits.filter(account__account_type=Account.PERSONAL,
                                                   date__gte=self.current_month,
                                                   date__lt=next_month)
        last_two_months_splits = context['category'].splits.filter(
            account__account_type=Account.PERSONAL,
            date__gte=two_months_ago, date__lt=self.current_month)
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

        context['current_month'] = self.current_month
        context['previous_month'] = last_month
        context['next_month'] = self.current_month + relativedelta(months=1)
        context['month_before'] = two_months_ago

        return context
