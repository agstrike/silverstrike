from django.test import TestCase

from silverstrike.models import Account


class AccountQuerysetTests(TestCase):
    def setUp(self):
        self.personal = Account.objects.create(name='Personal')
        self.foreign = Account.objects.create(name='foreign', account_type=Account.FOREIGN)

    def test_personal_queryset(self):
        queryset = Account.objects.personal()
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset.first(), self.personal)

    def test_foreign_queryset(self):
        queryset = Account.objects.foreign()
        self.assertEquals(queryset.count(), 1)
        self.assertEquals(queryset.first(), self.foreign)

    def test_active_queryset(self):
        queryset = Account.objects.active()
        # since foreign and system account are also active they are returned here
        self.assertEquals(queryset.count(), 3)
        self.personal.active = False
        self.personal.save()
        # now it should only be two
        queryset = Account.objects.active()
        self.assertEquals(queryset.count(), 2)

    def test_inactive_queryset(self):
        queryset = Account.objects.inactive()
        self.assertEquals(queryset.count(), 0)
        self.personal.active = False
        self.personal.save()

        queryset = Account.objects.inactive()
        self.assertEquals(queryset.count(), 1)
