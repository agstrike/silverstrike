from django.http import JsonResponse

from .models import Account, InternalAccountType


def get_accounts(request, account_type):
    account_type = getattr(InternalAccountType, account_type).value
    accounts = list(Account.objects.filter(
        internal_type=account_type).values_list('name', flat=True))
    return JsonResponse(accounts, safe=False)
