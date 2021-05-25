from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat import unittest
from ansible.modules.systemd import parse_systemctl_show


class ParseSystemctlShowTestCase(unittest.TestCase):

    def test_simple(self):
        lines = [
            'Type=simple',
            'Restart=no',
            'Requires=system.slice sysinit.target',
            'Description=Blah blah blah',
        ]
        parsed = parse_systemctl_show(lines)
        self.assertEqual(parsed, {
            'Type': 'simple',
            'Restart': 'no',
            'Requires': 'system.slice sysinit.target',
            'Description': 'Blah blah blah',
        })

    def test_multiline_exec(self):
        # This was taken from a real service that specified "ExecStart=/bin/echo foo\nbar"
        lines = [
            'Type=simple',
            'ExecStart={ path=/bin/echo ; argv[]=/bin/echo foo',
            'bar ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }',
            'Description=blah',
        ]
        parsed = parse_systemctl_show(lines)
        self.assertEqual(parsed, {
            'Type': 'simple',
            'ExecStart': '{ path=/bin/echo ; argv[]=/bin/echo foo\n'
                         'bar ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }',
            'Description': 'blah',
        })

    def test_single_line_with_brace(self):
        lines = [
            'Type=simple',
            'Description={ this is confusing',
            'Restart=no',
        ]
        parsed = parse_systemctl_show(lines)
        self.assertEqual(parsed, {
            'Type': 'simple',
            'Description': '{ this is confusing',
            'Restart': 'no',
        })
