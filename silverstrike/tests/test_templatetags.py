from django.test import TestCase

from silverstrike.templatetags import tags


class TemplateTagsTest(TestCase) :

    def test_dateformat_py2js_tag(self):
        test_cases = (
            ('%d/%m/%Y', 'dd/mm/yyyy'),
            ('%Y-%m-%d', 'yyyy-mm-dd')
        )

        for py_format, js_format in test_cases:
            self.assertEqual(tags.dateformat_py2js(py_format), js_format)

