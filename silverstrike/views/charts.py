from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

from silverstrike.lib import last_day_of_month


class ChartView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'silverstrike/charts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'charts'
        context['today'] = date.today()
        currentMonth = date.today().month
        currentYear = date.today().year
        minus_3_m = currentMonth - 3
        minus_3_y = currentYear
        if minus_3_m < 1:
            minus_3_m += 12
            minus_3_y -= 1
        minus_6_m = currentMonth - 6
        minus_6_y = currentYear
        if minus_6_m < 1:
            minus_6_m += 12
            minus_6_y -= 1
        context['minus_3_months'] = date.today().replace(month=minus_3_m, year=minus_3_y)
        context['minus_6_months'] = date.today().replace(month=minus_6_m, year=minus_6_y)
        context['minus_12_months'] = date.today().replace(year=currentYear - 1)

        context['first_day_of_month'] = date.today().replace(day=1)
        context['last_day_of_month'] = last_day_of_month(date.today())
        return context
