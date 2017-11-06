from datetime import date

from dateutil.relativedelta import relativedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

from silverstrike.lib import last_day_of_month


class ChartView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'silverstrike/charts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'charts'
        context['today'] = date.today()
        context['minus_3_months'] = date.today() - relativedelta(months=3)
        context['minus_6_months'] = date.today() - relativedelta(months=6)
        context['minus_12_months'] = date.today() - relativedelta(years=1)

        context['first_day_of_month'] = date.today().replace(day=1)
        context['last_day_of_month'] = last_day_of_month(date.today())
        return context
