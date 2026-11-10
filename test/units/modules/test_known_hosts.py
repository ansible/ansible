from __future__ import annotations

import base64
import hashlib
import hmac
import os
import tempfile

import unittest

from ansible.module_utils import basic
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_bytes
from ansible.modules.known_hosts import (
    compute_diff,
    hash_host_key,
    key_entry_matches_host,
    sanity_check,
)


class _SanityCheckFailed(Exception):
    """Raised by the stubbed ``fail_json`` to stop execution like the real one does."""


class KnownHostsDiffTestCase(unittest.TestCase):

    def _create_file(self, content):
        tmp_file = tempfile.NamedTemporaryFile(prefix='ansible-test-', suffix='-known_hosts', delete=False)
        tmp_file.write(to_bytes(content))
        tmp_file.close()
        self.addCleanup(os.unlink, tmp_file.name)
        return tmp_file.name

    def test_no_existing_file(self):
        path = "/tmp/this_file_does_not_exists_known_hosts"
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


class KnownHostsSanityCheckTestCase(unittest.TestCase):

    def _module(self):
        basic._load_params = lambda: {}
        module = AnsibleModule(argument_spec={})
        failure = {}

        def fail_json(msg, **kwargs):
            failure.update(kwargs, msg=msg)
            raise _SanityCheckFailed()

        module.fail_json = fail_json
        return module, failure

    def test_sanity_check_cleartext_match(self):
        module, _failure = self._module()
        host = '10.0.0.1'
        key = '%s ssh-rsa ASDF foo@bar' % (host,)
        sanity_check(module, host, key)

    def test_sanity_check_cleartext_alias_list(self):
        module, _failure = self._module()
        key = 'host.example.com,10.0.0.1 ssh-rsa ASDF'
        sanity_check(module, 'host.example.com', key)
        sanity_check(module, '10.0.0.1', key)

    def test_sanity_check_host_mismatch(self):
        module, failure = self._module()
        with self.assertRaises(_SanityCheckFailed):
            sanity_check(module, '10.0.0.1', 'other.example.com ssh-rsa ASDF')
        self.assertEqual(failure['msg'], 'Host parameter does not match hashed host field in supplied key')

    def test_sanity_check_hashed_match(self):
        module, _failure = self._module()
        host = 'host.example.com'
        key = hash_host_key(host, '%s ssh-rsa ASDF' % host)
        self.assertTrue(key.startswith('|1|') or '|1|' in key)
        sanity_check(module, host, key)

    def test_sanity_check_hashed_mismatch(self):
        module, failure = self._module()
        key = hash_host_key('host.example.com', 'host.example.com ssh-rsa ASDF')
        with self.assertRaises(_SanityCheckFailed):
            sanity_check(module, 'other.example.com', key)
        self.assertEqual(failure['msg'], 'Host parameter does not match hashed host field in supplied key')

    def test_key_entry_matches_host_helpers(self):
        host = 'example.com'
        salt = os.urandom(20)
        digest = hmac.new(salt, to_bytes(host), hashlib.sha1).digest()
        hashed = '|1|%s|%s' % (
            base64.b64encode(salt).decode(),
            base64.b64encode(digest).decode(),
        )
        self.assertTrue(key_entry_matches_host(host, '%s ssh-rsa AAAA' % hashed))
        self.assertFalse(key_entry_matches_host('other.com', '%s ssh-rsa AAAA' % hashed))
        self.assertTrue(key_entry_matches_host(host, 'example.com,10.0.0.1 ssh-rsa AAAA'))
        self.assertFalse(key_entry_matches_host(host, ''))
        self.assertFalse(key_entry_matches_host(host, '# comment'))
