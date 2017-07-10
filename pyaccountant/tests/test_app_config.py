from django.test import TestCase

from pyaccountant.apps import PyAccountantConfig


class AppConfigTest(TestCase):
    def test(self):
        self.assertEquals(PyAccountantConfig.name, 'pyaccountant')
