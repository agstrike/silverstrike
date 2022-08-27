from django.db import models
from django.db.models.functions.datetime import TruncMonth
from django.views import generic

from silverstrike.models import Split


class ReportView(generic.TemplateView):
    template_name = 'silverstrike/reports.html'


class IncomeExpenseReport(generic.TemplateView):
    template_name = 'silverstrike/income_expense_report.html'

    def get_context_data(self, **kwargs):
        context = super(IncomeExpenseReport, self).get_context_data(**kwargs)
        queryset = Split.objects.past().order_by()
        incomes = queryset.income().annotate(m=TruncMonth('date')).values('m').annotate(
            total=models.Sum('amount'))
        expenses = queryset.expense().annotate(m=TruncMonth('date')).values('m').annotate(
            total=models.Sum('amount'))
        result = []
        for i, e in zip(incomes, expenses):
            result.append({
                'month': i['m'],
                'income': round(i['total'], 2),
                'expense': round(e['total'], 2),
                'total': round(i['total'] + e['total'], 2)
            })
        context['result'] = result
        return context
