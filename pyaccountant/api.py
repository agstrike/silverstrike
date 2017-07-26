from django.http import JsonResponse

from .models import Account


def get_accounts(request, account_type):
    account_type = getattr(Account, account_type)
    accounts = list(Account.objects.filter(
        internal_type=account_type).values_list('name', flat=True))
    return JsonResponse(accounts, safe=False)
