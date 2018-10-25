import os

from django.test import TestCase

from silverstrike.importers.firefly import import_firefly


class FireFlyImportTests(TestCase):
    def setUp(self):
        super(FireFlyImportTests, self).setUp()
        self.csv_file = os.path.join(
            os.path.dirname(__file__),
            'fixtures',
            'firefly.csv')

    def test_single_import(self):
        import_firefly(self.csv_file)
