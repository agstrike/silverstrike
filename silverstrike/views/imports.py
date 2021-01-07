import csv
import json
from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from silverstrike import forms
from silverstrike import importers
from silverstrike import models


def _update_account(account, data):
    ibans = json.loads(account.import_ibans)
    names = json.loads(account.import_names)
    save = False
    if data.iban and data.iban not in ibans:
        ibans.append(data.iban)
        account.import_ibans = json.dumps(ibans)
        save = True
    if data.account and data.account not in names:
        names.append(data.account)
        account.import_names = json.dumps(names)
        save = True
    if save:
        account.save()


class ImportView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'silverstrike/import.html'


class ImportUploadView(LoginRequiredMixin, generic.edit.CreateView):
    model = models.ImportFile
    form_class = forms.ImportUploadForm
    template_name = 'silverstrike/import_upload.html'

    def form_valid(self, form):
        self.object = form.save()
        return HttpResponseRedirect(
            reverse('import_process', args=[self.object.pk]))


class ImportProcessView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'silverstrike/import_configure_upload.html'

    def get_context_data(self, **kwargs):
        context = super(ImportProcessView, self).get_context_data(**kwargs)
        file = models.ImportFile.objects.get(uuid=self.kwargs['uuid'])
        importer = file.importer
        iban_accounts = dict()
        names = dict()
        for a in models.Account.objects.all():
            try:
                for iban in json.loads(a.import_ibans):
                    iban_accounts[iban] = a
            except json.decoder.JSONDecodeError:
                pass
            try:
                for name in json.loads(a.import_names):
                    if name in names and names[name] != a:
                        del names[name]
                        continue
                    names[name] = a
            except json.decoder.JSONDecodeError:
                pass
        context['data'] = importers.IMPORTERS[importer].import_transactions(file.file.path)
        max_date = date(1970, 1, 1)
        min_date = date(3000, 1, 1)
        for datum in context['data']:
            if datum.book_date < min_date:
                min_date = datum.book_date
            if datum.book_date > max_date:
                max_date = datum.book_date
            if datum.iban and datum.iban in iban_accounts:
                datum.suggested_account = iban_accounts[datum.iban]
            elif datum.account in names:
                datum.suggested_account = names[datum.account]

        # duplicate detection
        transactions = set()
        for t in models.Transaction.objects.date_range(min_date, max_date):
            if t.is_transfer:
                transactions.add('{}-{}-{}'.format(t.src_id, t.date, t.amount))
                transactions.add('{}-{}-{}'.format(t.dst_id, t.date, t.amount))
            elif t.is_deposit:
                transactions.add('{}-{}-{}'.format(t.src_id, t.date, t.amount))
            elif t.is_withdraw:
                transactions.add('{}-{}-{}'.format(t.dst_id, t.date, t.amount))
        for datum in context['data']:
            if hasattr(datum, 'suggested_account') and '{}-{}-{:.2f}'.format(
                    datum.suggested_account.id, datum.book_date, abs(datum.amount)) in transactions:
                datum.ignore = True

        context['recurrences'] = models.RecurringTransaction.objects.exclude(
            interval=models.RecurringTransaction.DISABLED).order_by('title')
        return context

    def post(self, request, *args, **kwargs):
        file = models.ImportFile.objects.get(uuid=self.kwargs['uuid'])
        importer = file.importer
        data = importers.IMPORTERS[importer].import_transactions(file.file.path)
        for i in range(len(data)):
            title = request.POST.get('title-{}'.format(i), '')
            account = request.POST.get('account-{}'.format(i), '')
            recurrence = int(request.POST.get('recurrence-{}'.format(i), '-1'))
            ignore = request.POST.get('ignore-{}'.format(i), '')
            book_date = data[i].book_date
            date = data[i].transaction_date
            if not (title and account) or ignore:
                continue
            amount = float(data[i].amount)
            if amount == 0:
                continue
            account, _ = models.Account.objects.get_or_create(
                name=account,
                defaults={'account_type': models.Account.AccountType.FOREIGN})
            _update_account(account, data[i])
            if not account.iban and hasattr(data[i], 'iban'):
                account.iban = data[i].iban
                account.save()
            transaction = models.Transaction()
            if account.account_type == models.Account.AccountType.PERSONAL:
                transaction.transaction_type = models.Transaction.TRANSFER
                if amount < 0:
                    transaction.src_id = file.account_id
                    transaction.dst = account
                else:
                    transaction.src = account
                    transaction.dst_id = file.account_id
            elif account.account_type == models.Account.AccountType.FOREIGN:
                if amount < 0:
                    transaction.transaction_type = models.Transaction.WITHDRAW
                    transaction.src_id = file.account_id
                    transaction.dst = account
                else:
                    transaction.transaction_type = models.Transaction.DEPOSIT
                    transaction.dst_id = file.account_id
                    transaction.src = account
            transaction.title = title
            transaction.date = date
            transaction.amount = abs(amount)

            if recurrence > 0:
                transaction.recurrence_id = recurrence
            transaction.save()

            models.Split.objects.create(
                title=title,
                amount=amount,
                date=book_date,
                transaction=transaction,
                account_id=file.account_id,
                opposing_account=account
                )
            models.Split.objects.create(
                title=title,
                amount=-amount,
                date=date,
                transaction=transaction,
                account=account,
                opposing_account_id=file.account_id
                )
        return HttpResponseRedirect('/')


class ImportFireflyView(LoginRequiredMixin, generic.edit.CreateView):
    model = models.ImportFile
    fields = ['file']
    template_name = 'silverstrike/import_upload.html'

    def form_valid(self, form):
        self.object = form.save()
        importers.firefly.import_firefly(self.object.file.path)
        return HttpResponseRedirect(reverse('index'))


class ExportView(LoginRequiredMixin, generic.edit.FormView):
    template_name = 'silverstrike/export.html'
    form_class = forms.ExportForm

    def form_valid(self, form):
        response = HttpResponse(content_type='text/csv')

        splits = models.Split.objects.date_range(
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
