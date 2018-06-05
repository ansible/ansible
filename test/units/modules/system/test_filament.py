from ansible.compat.tests import unittest
from ansible.modules.system import filament


class TestFilament(unittest.TestCase):
    def test_add(self):
        op_a = 1
        op_b = 2
        result = filament.add(op_a, op_b)
        self.assertEqual(result, 3)

        op_a = "abc"
        op_b = "def"
        result = filament.add(op_a, op_b)
        self.assertEqual(result, 'abcdef')

        op_a = True
        op_b = True
        result = filament.add(op_a, op_b)
        self.assertEqual(result, 2)
