import os
from datetime import date
from unittest import skipUnless

from django.test import TestCase

from silverstrike import importers


class ImportTests(TestCase):
    def setUp(self):
        super(ImportTests, self).setUp()
        self.base_dir = os.path.join(os.path.dirname(__file__), 'fixtures')

    def test_firefly_import(self):
        importers.firefly.import_firefly(os.path.join(self.base_dir, 'firefly.csv'))

    def test_pc_mastercard(self):
        transactions = importers.pc_mastercard.import_transactions(
            os.path.join(self.base_dir, 'president-choice-mastercard.csv'))
        self.assertEqual(len(transactions), 4)
        t = transactions[0]
        self.assertEqual(t.amount, -40.03)
        self.assertEqual(t.book_date, date(2018, 10, 18))

    @skipUnless(hasattr(importers, 'ofx'), 'ofxparse is not installed')
    def test_ofx(self):
        transactions = importers.ofx.import_transactions(
            os.path.join(self.base_dir, 'ofx.qfx'))
        t = transactions[0]
        self.assertEqual(t.amount, 34.50)
        self.assertEqual(t.book_date, date(2018, 1, 2))
