from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

from pyaccountant.models import Category


class CategoryIndex(LoginRequiredMixin, generic.ListView):
    template_name = 'pyaccountant/category_index.html'
    context_object_name = 'categories'
    model = Category

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['menu'] = 'categories'
        return context
