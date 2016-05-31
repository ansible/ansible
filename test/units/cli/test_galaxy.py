"""
import unittest
from ansible.cli.galaxy import GalaxyCLI

class TestGalaxyCli(unittest.TestCase):

    def test_display_role_info(self):
        x = GalaxyCLI("foo")
        role_info = {'name':'foo', 'description':'bar'}
        y = x._display_role_info(role_info)
        
        assert(y == u'\nRole: foo\n\tdescription: bar')
"""
