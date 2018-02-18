from django.test import TestCase

from silverstrike.models import Account


class ReconaliationForm(TestCase):
    def setUp(self):
        self.account = Account.objects.create(name='personal')
