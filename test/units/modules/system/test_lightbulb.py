from ansible.compat.tests import unittest
from ansible.modules.system.lightbulb import add


class LightbulbAddTestCase(unittest.TestCase):

    def test_int(self):
        result = add(3, 3)
        self.assertEqual(result, 6)

    def test_double(self):
        result = add(2.0, 4.0)
        self.assertEqual(result, 6.0)

    def test_string(self):
        result = add("Hello, my name is ", "fostimus, nice to meet you!")
        self.assertEqual(result, "Hello, my name is fostimus, nice to meet you!")

    def test_boolean(self):
        result = add(True, True)
        self.assertEqual(result, 2)

        result = add(False, False)
        self.assertEqual(result, False)
        self.assertEqual(result, 0)

        result = add(True, False)
        self.assertEqual(result, True)
        self.assertEqual(result, 1)

    def test_nonetype(self):
        result = add(None, None)
        self.assertEqual(result, "NoneTypeNoneType")

