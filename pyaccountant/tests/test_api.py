import json

from django.test import TestCase
from django.urls import reverse

from pyaccountant.models import Account


class ApiTests(TestCase):
    def setUp(self):
        Account.objects.bulk_create(
            [Account(name=t[1], internal_type=t[0]) for t in Account.ACCOUNT_TYPES])

    def test_get_accounts_return_value(self):
        for t in Account.ACCOUNT_TYPES:
            response = self.client.get(reverse('api_accounts', args=[t[1].upper()]))
            data = json.loads(response.content.decode('utf-8'))
            self.assertEquals(data, list(Account.objects.filter(
                internal_type=t[0]).values_list('name', flat=True)))
