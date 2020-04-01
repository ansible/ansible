from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest

from ansible.modules.system.filament import do_add


class TestFilament(unittest.TestCase):

    def test_do_add(self):
        self.assertEqual(10, do_add(6, 4))
