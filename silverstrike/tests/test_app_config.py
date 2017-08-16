from django.test import TestCase

from silverstrike.apps import SilverStrikeConfig


class AppConfigTest(TestCase):
    def test(self):
        self.assertEquals(SilverStrikeConfig.name, 'silverstrike')
