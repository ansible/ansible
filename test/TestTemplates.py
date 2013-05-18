import unittest
from ansible.utils import template
from ansible.errors import AnsibleError
import ansible.constants as C

CURRENT_VAL = str(C.DEFAULT_JINJA2_UNDEFINED)

class TestUndefinedTemplateVarible(unittest.TestCase):

    def tearDown(self):
        C.DEFAULT_JINJA2_UNDEFINED = CURRENT_VAL

    def test_undefined_var_raises_error_when_strict(self):
        C.DEFAULT_JINJA2_UNDEFINED = 'strict'
        self.assertRaises(
            AnsibleError,
            template.template_from_string,
            '.', '{{ undefined_var }}', {},
        )

    def test_undefined_var_noops_when_noop(self):
        C.DEFAULT_JINJA2_UNDEFINED = 'noop'
        templ = '{{ undefined_var }}'
        res = template.template_from_string('.', templ, {})
        self.assertEqual(res, templ)

