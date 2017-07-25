from ansible.compat.tests import unittest
from ansible.modules.system.lightbulb import add_things


class LightbulbTestCase(unittest.TestCase):

    def test_add_things(self):
        out = add_things(1, 2)
        self.assertEqual(out, 3)
