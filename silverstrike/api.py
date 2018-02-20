import datetime

from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse

from .models import Account, Split


@login_required
def get_accounts(request, account_type):
    accounts = Account.objects.exclude(account_type=Account.SYSTEM)
    if account_type != 'all':
        account_type = getattr(Account, account_type)
        accounts = accounts.filter(account_type=account_type)

    return JsonResponse(list(accounts.values_list('name', flat=True)), safe=False)


@login_required
def get_accounts_balance(request, dstart, dend):
    dstart = datetime.datetime.strptime(dstart, '%Y-%m-%d').date()
    dend = datetime.datetime.strptime(dend, '%Y-%m-%d').date()
    dataset = []
    for account in Account.objects.personal().active():
        data = list(zip(*account.get_data_points(dstart, dend)))
        dataset.append({'name': account.name, 'data': data[1]})
    if dataset:
        labels = [datetime.datetime.strftime(x, '%d %b %Y') for x in data[0]]
    else:
        labels = []
    return JsonResponse({'labels': labels, 'dataset': dataset})


@login_required
def get_account_balance(request, account_id, dstart, dend):
    dstart = datetime.datetime.strptime(dstart, '%Y-%m-%d').date()
    dend = datetime.datetime.strptime(dend, '%Y-%m-%d').date()
    account = Account.objects.get(pk=account_id)
    labels, data = zip(*account.get_data_points(dstart, dend))
    return JsonResponse({'data': data, 'labels': labels})


@login_required
def get_balances(request, dstart, dend):
    dstart = datetime.datetime.strptime(dstart, '%Y-%m-%d').date()
    dend = datetime.datetime.strptime(dend, '%Y-%m-%d').date()
    balance = Split.objects.personal().exclude_transfers().filter(date__lt=dstart).aggregate(
            models.Sum('amount'))['amount__sum'] or 0
    splits = Split.objects.personal().exclude_transfers().date_range(dstart, dend).order_by('date')
    data_points = []
    labels = []
    days = (dend - dstart).days
    if days > 50:
        step = days / 50 + 1
    else:
        step = 1
    for split in splits:
        while split.date > dstart:
            data_points.append(balance)
            labels.append(datetime.datetime.strftime(dstart, '%Y-%m-%d'))
            dstart += datetime.timedelta(days=step)
        balance += split.amount
    data_points.append(balance)
    labels.append(datetime.datetime.strftime(dend, '%Y-%m-%d'))
    return JsonResponse({'labels': labels, 'data': data_points})


@login_required
def category_spending(request, dstart, dend):
    dstart = datetime.datetime.strptime(dstart, '%Y-%m-%d')
    dend = datetime.datetime.strptime(dend, '%Y-%m-%d')
    res = Split.objects.expense().past().date_range(dstart, dend).order_by('category').values(
        'category__name').annotate(spent=models.Sum('amount'))
    if res:
        res = [(e['category__name'] or 'No category', abs(e['spent'])) for e in res if e['spent']]
        categories, spent = zip(*res)
    else:
        categories, spent = [], []
    return JsonResponse({'categories': categories, 'spent': spent})
