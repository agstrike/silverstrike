import datetime

from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from .models import Account, RecurringTransaction


def get_accounts(request, account_type):
    accounts = Account.objects.exclude(internal_type=Account.SYSTEM)
    if account_type != 'all':
        account_type = getattr(Account, account_type)
        accounts = accounts.filter(internal_type=account_type)

    return JsonResponse(list(accounts.values_list('name', flat=True)), safe=False)


def get_accounts_balance(request, dstart, dend):
    delta = datetime.timedelta(days=3)
    dstart = datetime.datetime.strptime(dstart, '%Y-%m-%d') - delta
    dend = datetime.datetime.strptime(dend, '%Y-%m-%d') + delta
    dataset = []
    for account in Account.objects.filter(internal_type=Account.PERSONAL, show_on_dashboard=True):
        data = list(zip(*account.get_data_points(dstart, dend)))
        dataset.append({'name': account.name, 'data': data[1]})
    if dataset:
        labels = [datetime.datetime.strftime(x, '%d %b %Y') for x in data[0]]
    else:
        labels = []
    return JsonResponse({'labels': labels, 'dataset': dataset})


@require_POST
def skip_recurrence(request, pk):
    recurrence = get_object_or_404(RecurringTransaction, pk=pk)
    recurrence.update_date()
    return HttpResponseRedirect(request.GET['next'])
