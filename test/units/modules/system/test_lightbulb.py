from ansible.compat.tests import unittest
from ansible.modules.system.lightbulb import add


class AddTestCase(unittest.TestCase):

    def test_ints(self):
        ret_val = add(2, 3)
        self.assertEqual(ret_val, 2 + 3)

    def test_strings(self):
        ret_val = add('hello', ' world')
        self.assertEqual(ret_val, 'hello world')

    def test_bools(self):
        ret_val = add(True, False)
        self.assertEqual(ret_val, True)
