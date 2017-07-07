import json

from django.test import TestCase
from django.urls import reverse

from pyaccountant.models import Account, InternalAccountType


class ApiTests(TestCase):
    def setUp(self):
        Account.objects.bulk_create(
            [Account(name=t.name, internal_type=t.value) for t in InternalAccountType])

    def test_get_accounts_return_value(self):
        for t in InternalAccountType:
            response = self.client.get(reverse('api_accounts', args=[t.name]))
            data = json.loads(response.content.decode('utf-8'))
            self.assertEquals(data, list(Account.objects.filter(
                internal_type=t.value).values_list('name', flat=True)))
