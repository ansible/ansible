import unittest
from ansible.utils import template
from ansible.errors import AnsibleError

class TestUndefinedTemplateVarible(unittest.TestCase):

    def test_undefined_var_raises_error(self):
        self.assertRaises(
            AnsibleError,
            template.template_from_string,
            '.', '{{ undefined_var }}', {},
        )
