import csv

from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import formset_factory
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from pyaccountant.forms import CSVDefinitionForm, ImportUploadForm
from pyaccountant.lib import import_csv, import_firefly
from pyaccountant.models import ImportConfiguration, ImportFile


class ImportView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'pyaccountant/import.html'


class ImportFireflyView(LoginRequiredMixin, generic.edit.CreateView):
    model = ImportFile
    fields = ['file']
    template_name = 'pyaccountant/import_upload.html.j2'

    def form_valid(self, form):
        self.object = form.save()
        import_firefly(self.object.file.path)
        return HttpResponseRedirect(reverse('index'))


class ImportUploadView(LoginRequiredMixin, generic.edit.CreateView):
    template_name = 'pyaccountant/import_upload.html.j2'
    model = ImportFile
    form_class = ImportUploadForm

    def form_valid(self, form):
        self.configuration = form.cleaned_data['configuration']
        return super().form_valid(form)

    def get_success_url(self):
        if self.configuration:
            return reverse('import_process', args=[self.object.pk, self.configuration.pk])
        else:
            return reverse('import_configure', args=(self.object.pk,))


class ImportConfigureView(LoginRequiredMixin, generic.CreateView):
    model = ImportConfiguration
    template_name = 'pyaccountant/import_configure.html.j2'
    fields = ['name', 'headers', 'default_account']

    def get_success_url(self):
        return reverse('import_process', args=[self.kwargs['uuid'], self.object.pk])

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        formset = self.get_form(formset_factory(CSVDefinitionForm))
        if formset.is_valid() and form.is_valid():
            # process formset here
            col_types = ' '.join([f.cleaned_data['field_type'] for f in formset])
            self.object = form.save(commit=False)
            self.object.config = col_types
            self.object.save()
            import_csv(ImportFile.objects.get(uuid=self.kwargs['uuid']).file.path, self.object)
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        file = ImportFile.objects.get(uuid=self.kwargs['uuid']).file
        data = []
        for line in csv.reader(open(file.path)):
            data.append(line)
            if len(data) > 19:
                break
        context['data'] = data
        context['formset'] = formset_factory(CSVDefinitionForm, extra=len(data[0]))
        return context


class ImportProcessView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'pyaccountant/import_process.html.j2'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        file = ImportFile.objects.get(uuid=self.kwargs['uuid']).file
        data = []
        for line in csv.reader(open(file.path)):
            data.append(line)
        context['data'] = data
        return context
