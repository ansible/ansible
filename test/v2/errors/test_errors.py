# TODO: header

import unittest

from mock import mock_open, patch

from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject
from ansible.errors import AnsibleError

class TestErrors(unittest.TestCase):

    def setUp(self):
        self.message = 'this is the error message'

    def tearDown(self):
        pass

    def test_basic_error(self):
        e = AnsibleError(self.message)
        assert e.message == self.message

    def test_error_with_object(self):
        obj = AnsibleBaseYAMLObject()
        obj._data_source   = 'foo.yml'
        obj._line_number   = 1
        obj._column_number = 1

        m = mock_open()
        m.return_value.readlines.return_value = ['this is line 1\n', 'this is line 2\n', 'this is line 3\n']
        with patch('__builtin__.open', m):
            e = AnsibleError(self.message, obj)

        assert e.message == 'this is the error message\nThe error occurred on line 1 of the file foo.yml:\nthis is line 1\n^'
