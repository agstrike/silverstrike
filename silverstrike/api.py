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
    dstart = datetime.datetime.strptime(dstart, '%Y-%m-%d')
    dend = datetime.datetime.strptime(dend, '%Y-%m-%d')
    dataset = []
    for account in Account.objects.filter(account_type=Account.PERSONAL):
        data = list(zip(*account.get_data_points(dstart, dend)))
        dataset.append({'name': account.name, 'data': data[1]})
    if dataset:
        labels = [datetime.datetime.strftime(x, '%d %b %Y') for x in data[0]]
    else:
        labels = []
    return JsonResponse({'labels': labels, 'dataset': dataset})


@login_required
def get_balances(request, dstart, dend):
    dstart = datetime.datetime.strptime(dstart, '%Y-%m-%d')
    dend = datetime.datetime.strptime(dend, '%Y-%m-%d')
    balance = Split.objects.personal().filter(date__lte=dstart).aggregate(
            models.Sum('amount'))['amount__sum'] or 0
    splits = Split.objects.personal().date_range(dstart, dend)
    splits = list(splits.order_by('-date'))

    steps = 30
    step = (dend - dstart) / steps
    if step < datetime.timedelta(days=1):
        step = datetime.timedelta(days=1)
        steps = int((dend - dstart) / step)
    data_points = []
    labels = []
    for i in range(steps):
        while len(splits) > 0 and splits[-1].date <= dstart.date():
            t = splits.pop()
            balance += t.amount
        labels.append(datetime.datetime.strftime(dstart, '%Y-%m-%d'))
        data_points.append(balance)
        dstart += step
    for s in splits:
        balance += s.amount
        labels.append(datetime.datetime.strftime(dstart, '%Y-%m-%d'))
    data_points.append(balance)
    return JsonResponse({'labels': labels, 'data': data_points})


@login_required
def category_spending(request, dstart, dend):
    dstart = datetime.datetime.strptime(dstart, '%Y-%m-%d')
    dend = datetime.datetime.strptime(dend, '%Y-%m-%d')
    res = Split.objects.expense().past().date_range(dstart, dend).order_by('category').values(
        'category__name').annotate(spent=models.Sum('amount'))
    res = [(e['category__name'] or 'No category', abs(e['spent'])) for e in res if e['spent']]
    categories, spent = zip(*res)
    return JsonResponse({'categories': categories, 'spent': spent})
