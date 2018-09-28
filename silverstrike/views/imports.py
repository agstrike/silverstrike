import csv
import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views import generic

from silverstrike.forms import CSVDefinitionForm, ExportForm, ImportUploadForm
from silverstrike.lib import import_csv, import_firefly
from silverstrike.models import ImportConfiguration, ImportFile, Split
from silverstrike import models
from silverstrike.importers import dkb


class ImportView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'silverstrike/import.html'


class ImportFireflyView(LoginRequiredMixin, generic.edit.CreateView):
    model = ImportFile
    fields = ['file']
    template_name = 'silverstrike/import_upload.html'

    def form_valid(self, form):
        self.object = form.save()
        import_firefly(self.object.file.path)
        return HttpResponseRedirect(reverse('index'))


class ImportDKBView(LoginRequiredMixin, generic.edit.CreateView):
    model = ImportFile
    fields = ['file']
    template_name = 'silverstrike/import_upload.html'

    def get_success_url(self):
        return reverse('import_process_dkb', args=[self.object.pk, self.kwargs['account']])


class ImportProcessDKB(LoginRequiredMixin, generic.TemplateView):
    template_name = 'silverstrike/import_configure_upload.html'

    def get_context_data(self, **kwargs):
        context = super(ImportProcessDKB, self).get_context_data(**kwargs)
        file = ImportFile.objects.get(uuid=self.kwargs['uuid'])
        context['data'] = dkb.import_csv(file.file.path)
        context['recurrences'] = models.RecurringTransaction.objects.exclude(recurrence=models.RecurringTransaction.DISABLED)
        return context

    def post(self, request, *args, **kwargs):
        file = ImportFile.objects.get(uuid=self.kwargs['uuid'])
        data = dkb.import_csv(file.file.path)
        for i in range(1, len(data)):
            title = request.POST.get('title-{}'.format(i), '')
            account = request.POST.get('account-{}'.format(i), '')
            recurrence = int(request.POST.get('recurrence-{}'.format(i), '-1'))
            date = datetime.datetime.strptime(data[i][1], '%d.%m.%Y')
            if not (title or account):
                continue
            amount = float(data[i][4])
            if amount == 0:
                continue
            account = models.Account.objects.get(name=account)
            transaction_type = -1
            if account.account_type == models.Account.PERSONAL:
                transaction_type = models.Transaction.TRANSFER
            elif account.account_type == models.Account.FOREIGN:
                if amount < 0:
                    transaction_type = models.Transaction.WITHDRAW
                else:
                    transaction_type = models.Transaction.DEPOSIT
            transaction = models.Transaction()
            transaction.title = title
            transaction.date = date
            transaction.transaction_type = transaction_type
            if recurrence > 0:
                transaction.recurrence_id = recurrence
            transaction.save()

            s1 = models.Split.objects.create(
                title=title,
                amount=amount,
                date=date,
                transaction=transaction,
                account_id=self.kwargs['account'],
                opposing_account=account
                )
            s2 = models.Split.objects.create(
                title=title,
                amount=-amount,
                date=date,
                transaction=transaction,
                account=account,
                opposing_account_id=self.kwargs['account']
                )
            print(transaction.id)
            print(s1.id)
            print(s2.id)
        return HttpResponseRedirect('/')


class ImportUploadView(LoginRequiredMixin, generic.edit.CreateView):
    template_name = 'silverstrike/import_upload.html'
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
    template_name = 'silverstrike/import_configure.html'
    fields = ['name', 'headers', 'default_account', 'dateformat']

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
    template_name = 'silverstrike/import_process.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        file = ImportFile.objects.get(uuid=self.kwargs['uuid']).file
        data = []
        for line in csv.reader(open(file.path)):
            data.append(line)
        context['data'] = data
        return context


class ExportView(LoginRequiredMixin, generic.edit.FormView):
    template_name = 'silverstrike/export.html'
    form_class = ExportForm

    def form_valid(self, form):
        response = HttpResponse(content_type='text/csv')

        splits = Split.objects.date_range(
            form.cleaned_data['start'], form.cleaned_data['end']).transfers_once()
        splits = splits.filter(account__in=form.cleaned_data['accounts'])
        csv_writer = csv.writer(response, delimiter=';')
        headers = [
            'account',
            'opposing_account',
            'date',
            'amount',
            'category'
            ]
        csv_writer.writerow(headers)
        for split in splits.values_list('account__name', 'opposing_account__name',
                                        'date', 'amount', 'category__name'):
            csv_writer.writerow(split)

        response['Content-Disposition'] = 'attachment; filename=export.csv'
        return response
