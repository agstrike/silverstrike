from datetime import date

from dateutil.relativedelta import relativedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.urls import reverse_lazy
from django.views import generic

from silverstrike.forms import BudgetFormSet
from silverstrike.lib import last_day_of_month
from silverstrike.models import Budget, Category, Split


class BudgetIndex(LoginRequiredMixin, generic.edit.FormView):
    template_name = 'silverstrike/budget_index.html'
    context_object_name = 'formset'
    success_url = reverse_lazy('budgets')
    form_class = BudgetFormSet

    def dispatch(self, request, *args, **kwargs):
        if 'month' in kwargs:
            self.month = date(kwargs.pop('year'), kwargs.pop('month'), 1)
        else:
            self.month = date.today().replace(day=1)
        return super(BudgetIndex, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        # assigned categories
        budgets = Budget.objects.for_month(self.month)
        budget_spending = Split.objects.personal().past().date_range(
            self.month, last_day_of_month(self.month)).values(
                'category', 'category__name').annotate(spent=Sum('amount'))

        budget_spending = {e['category']: abs(e['spent']) for e in budget_spending}
        initial = []

        # existing budgets
        for budget in budgets:
            initial.append({
                'budget_id': budget.id,
                'category_id': budget.category_id,
                'category_name': budget.category.name,
                'spent': budget_spending.get(budget.category_id, 0),
                'amount': budget.amount,
                'left': - budget_spending.get(budget.category_id, 0) + budget.amount,
                'month': self.month,
            })

        ids = [budget.category_id for budget in budgets]
        for category in Category.objects.exclude(id__in=ids).exclude(active=False):
            initial.append({
                'budget_id': -1,
                'category_id': category.id,
                'category_name': category.name,
                'spent': budget_spending.get(category.id, 0),
                'amount': 0,
                'left': - budget_spending.get(category.id, 0),
                'month': self.month,
            })
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'budgets'
        context['month'] = self.month
        context['previous_month'] = self.month - relativedelta(months=1)
        context['next_month'] = self.month + relativedelta(months=1)
        return context

    def form_valid(self, form):
        for f in form:
            f.save()
        return super(BudgetIndex, self).form_valid(form)
