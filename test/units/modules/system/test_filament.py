import unittest

from ansible.modules.system.filament import do_add

class TestFilament(unittest.TestCase):

    def test_do_add(self):
        self.assertEqual(10, do_add(6, 4))