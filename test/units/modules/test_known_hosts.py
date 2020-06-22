from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import tempfile
from ansible.module_utils import basic

from units.compat import unittest
from ansible.module_utils._text import to_bytes
from ansible.module_utils.basic import AnsibleModule

from ansible.modules.known_hosts import compute_diff, sanity_check


class KnownHostsDiffTestCase(unittest.TestCase):

    def _create_file(self, content):
        tmp_file = tempfile.NamedTemporaryFile(prefix='ansible-test-', suffix='-known_hosts', delete=False)
        tmp_file.write(to_bytes(content))
        tmp_file.close()
        self.addCleanup(os.unlink, tmp_file.name)
        return tmp_file.name

    def test_no_existing_file(self):
        path = tempfile.mktemp(prefix='ansible-test-', suffix='-known_hosts')
        key = 'example.com ssh-rsa AAAAetc\n'
        diff = compute_diff(path, found_line=None, replace_or_add=False, state='present', key=key)
        self.assertEqual(diff, {
            'before_header': '/dev/null',
            'after_header': path,
            'before': '',
            'after': 'example.com ssh-rsa AAAAetc\n',
        })

    def test_key_addition(self):
        path = self._create_file(
            'two.example.com ssh-rsa BBBBetc\n'
        )
        key = 'one.example.com ssh-rsa AAAAetc\n'
        diff = compute_diff(path, found_line=None, replace_or_add=False, state='present', key=key)
        self.assertEqual(diff, {
            'before_header': path,
            'after_header': path,
            'before': 'two.example.com ssh-rsa BBBBetc\n',
            'after': 'two.example.com ssh-rsa BBBBetc\none.example.com ssh-rsa AAAAetc\n',
        })

    def test_no_change(self):
        path = self._create_file(
            'one.example.com ssh-rsa AAAAetc\n'
            'two.example.com ssh-rsa BBBBetc\n'
        )
        key = 'one.example.com ssh-rsa AAAAetc\n'
        diff = compute_diff(path, found_line=1, replace_or_add=False, state='present', key=key)
        self.assertEqual(diff, {
            'before_header': path,
            'after_header': path,
            'before': 'one.example.com ssh-rsa AAAAetc\ntwo.example.com ssh-rsa BBBBetc\n',
            'after': 'one.example.com ssh-rsa AAAAetc\ntwo.example.com ssh-rsa BBBBetc\n',
        })

    def test_key_change(self):
        path = self._create_file(
            'one.example.com ssh-rsa AAAaetc\n'
            'two.example.com ssh-rsa BBBBetc\n'
        )
        key = 'one.example.com ssh-rsa AAAAetc\n'
        diff = compute_diff(path, found_line=1, replace_or_add=True, state='present', key=key)
        self.assertEqual(diff, {
            'before_header': path,
            'after_header': path,
            'before': 'one.example.com ssh-rsa AAAaetc\ntwo.example.com ssh-rsa BBBBetc\n',
            'after': 'two.example.com ssh-rsa BBBBetc\none.example.com ssh-rsa AAAAetc\n',
        })

    def test_key_removal(self):
        path = self._create_file(
            'one.example.com ssh-rsa AAAAetc\n'
            'two.example.com ssh-rsa BBBBetc\n'
        )
        key = 'one.example.com ssh-rsa AAAAetc\n'
        diff = compute_diff(path, found_line=1, replace_or_add=False, state='absent', key=key)
        self.assertEqual(diff, {
            'before_header': path,
            'after_header': path,
            'before': 'one.example.com ssh-rsa AAAAetc\ntwo.example.com ssh-rsa BBBBetc\n',
            'after': 'two.example.com ssh-rsa BBBBetc\n',
        })

    def test_key_removal_no_change(self):
        path = self._create_file(
            'two.example.com ssh-rsa BBBBetc\n'
        )
        key = 'one.example.com ssh-rsa AAAAetc\n'
        diff = compute_diff(path, found_line=None, replace_or_add=False, state='absent', key=key)
        self.assertEqual(diff, {
            'before_header': path,
            'after_header': path,
            'before': 'two.example.com ssh-rsa BBBBetc\n',
            'after': 'two.example.com ssh-rsa BBBBetc\n',
        })

    def test_sanity_check(self):
        basic._load_params = lambda: {}
        # Module used internally to execute ssh-keygen system executable
        module = AnsibleModule(argument_spec={})
        host = '10.0.0.1'
        key = '%s ssh-rsa ASDF foo@bar' % (host,)
        keygen = module.get_bin_path('ssh-keygen')
        sanity_check(module, host, key, keygen)
