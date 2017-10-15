import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from silverstrike.models import Account


class ApiTests(TestCase):
    def setUp(self):
        User.objects.create_superuser(username='admin', email='email@example.com', password='pass')
        self.client.login(username='admin', password='pass')
        Account.objects.bulk_create(
            [Account(name=t[1], account_type=t[0],
                     show_on_dashboard=True) for t in Account.ACCOUNT_TYPES])

    def test_get_accounts_return_value(self):
        for t in Account.ACCOUNT_TYPES:
            response = self.client.get(reverse('api_accounts', args=[t[1].upper()]))
            data = json.loads(response.content.decode('utf-8'))
            queryset = Account.objects.filter(account_type=t[0])
            queryset = queryset.exclude(account_type=Account.SYSTEM)
            self.assertEquals(data, list(queryset.values_list('name', flat=True)))
