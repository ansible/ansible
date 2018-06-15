# (c) 2018, Scott Buchanan <sbuchanan@ri.pn>
# (c) 2016, Andrew Zenk <azenk@umn.edu> (test_lastpass.py used as starting point)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import datetime

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from argparse import ArgumentParser


from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch
from ansible.errors import AnsibleError
from ansible.plugins.lookup.onepassword import OnePass, LookupModule
from ansible.plugins.lookup.onepassword_raw import LookupModule as OnePasswordRawLookup


# Intentionally excludes metadata leaf nodes that would exist in real output if not relevant.
MOCK_ENTRIES = [
    {
        'vault_name': 'Acme "Quot\'d" Servers',
        'queries': [
            '0123456789',
            'Mock "Quot\'d" Server'
        ],
        'output': {
            'uuid': '0123456789',
            'vaultUuid': '2468',
            'overview': {
                'title': 'Mock "Quot\'d" Server'
            },
            'details': {
                'sections': [{
                    'title': '',
                    'fields': [
                        {'t': 'username', 'v': 'jamesbond'},
                        {'t': 'password', 'v': 't0pS3cret'},
                        {'t': 'notes', 'v': 'Test note with\nmultiple lines and trailing space.\n\n'},
                        {'t': 'tricksy "quot\'d" field\\', 'v': '"quot\'d" value'}
                    ]
                }]
            }
        }
    },
    {
        'vault_name': 'Acme Logins',
        'queries': [
            '9876543210',
            'Mock Website',
            'acme.com'
        ],
        'output': {
            'uuid': '9876543210',
            'vaultUuid': '1357',
            'overview': {
                'title': 'Mock Website',
                'URLs': [
                    {'l': 'website', 'u': 'https://acme.com/login'}
                ]
            },
            'details': {
                'sections': [{
                    'title': '',
                    'fields': [
                        {'t': 'password', 'v': 't0pS3cret'}
                    ]
                }]
            }
        }
    },
    {
        'vault_name': 'Acme Logins',
        'queries': [
            '864201357'
        ],
        'output': {
            'uuid': '864201357',
            'vaultUuid': '1357',
            'overview': {
                'title': 'Mock Something'
            },
            'details': {
                'fields': [
                    {
                        'value': 'jbond@mi6.gov.uk',
                        'name': 'emailAddress'
                    },
                    {
                        'name': 'password',
                        'value': 'vauxhall'
                    }
                ]
            }
        }
    },
]


def get_mock_query_generator(require_field=None):
    def _process_field(field, section_title=None):
        field_name = field.get('name', field.get('t'))
        field_value = field.get('value', field.get('v'))

        if require_field is None or field_name == require_field:
            return entry, query, section_title, field_name, field_value

    for entry in MOCK_ENTRIES:
        for query in entry['queries']:
            for field in entry['output']['details'].get('fields', []):
                fixture = _process_field(field)
                if fixture:
                    yield fixture
            for section in entry['output']['details'].get('sections', []):
                for field in section['fields']:
                    fixture = _process_field(field, section['title'])
                    if fixture:
                        yield fixture


def get_one_mock_query(require_field=None):
    generator = get_mock_query_generator(require_field)
    return next(generator)


class MockOnePass(OnePass):

    _mock_logged_out = False
    _mock_timed_out = False

    def _lookup_mock_entry(self, key, vault=None):
        for entry in MOCK_ENTRIES:
            if vault is not None and vault.lower() != entry['vault_name'].lower() and vault.lower() != entry['output']['vaultUuid'].lower():
                continue

            match_fields = [
                entry['output']['uuid'],
                entry['output']['overview']['title']
            ]

            # Note that exactly how 1Password matches on domains in non-trivial cases is neither documented
            # nor obvious, so this may not precisely match the real behavior.
            urls = entry['output']['overview'].get('URLs')
            if urls is not None:
                match_fields += [urlparse(url['u']).netloc for url in urls]

            if key in match_fields:
                return entry['output']

    def _run(self, args, expected_rc=0):
        parser = ArgumentParser()

        command_parser = parser.add_subparsers(dest='command')

        get_parser = command_parser.add_parser('get')
        get_options = ArgumentParser(add_help=False)
        get_options.add_argument('--vault')
        get_type_parser = get_parser.add_subparsers(dest='object_type')
        get_type_parser.add_parser('account', parents=[get_options])
        get_item_parser = get_type_parser.add_parser('item', parents=[get_options])
        get_item_parser.add_argument('item_id')

        args = parser.parse_args(args)

        def mock_exit(output='', error='', rc=0):
            if rc != expected_rc:
                raise AnsibleError(error)
            if error != '':
                now = datetime.date.today()
                error = '[LOG] {0} (ERROR) {1}'.format(now.strftime('%Y/%m/%d %H:$M:$S'), error)
            return output, error

        if args.command == 'get':
            if self._mock_logged_out:
                return mock_exit(error='You are not currently signed in. Please run `op signin --help` for instructions', rc=1)

            if self._mock_timed_out:
                return mock_exit(error='401: Authentication required.', rc=1)

            if args.object_type == 'item':
                mock_entry = self._lookup_mock_entry(args.item_id, args.vault)

                if mock_entry is None:
                    return mock_exit(error='Item {0} not found'.format(args.item_id))

                return mock_exit(output=json.dumps(mock_entry))

            if args.object_type == 'account':
                # Since we don't actually ever use this output, don't bother mocking output.
                return mock_exit()

        raise AnsibleError('Unsupported command string passed to OnePass mock: {0}'.format(args))


class LoggedOutMockOnePass(MockOnePass):

    _mock_logged_out = True


class TimedOutMockOnePass(MockOnePass):

    _mock_timed_out = True


class TestOnePass(unittest.TestCase):

    def test_onepassword_cli_path(self):
        op = MockOnePass(path='/dev/null')
        self.assertEqual('/dev/null', op.cli_path)

    def test_onepassword_logged_in(self):
        op = MockOnePass()
        try:
            op.assert_logged_in()
        except:
            self.fail()

    def test_onepassword_logged_out(self):
        op = LoggedOutMockOnePass()
        with self.assertRaises(AnsibleError):
            op.assert_logged_in()

    def test_onepassword_timed_out(self):
        op = TimedOutMockOnePass()
        with self.assertRaises(AnsibleError):
            op.assert_logged_in()

    def test_onepassword_get(self):
        op = MockOnePass()
        query_generator = get_mock_query_generator()
        for dummy, query, dummy, field_name, field_value in query_generator:
            self.assertEqual(field_value, op.get_field(query, field_name))

    def test_onepassword_get_raw(self):
        op = MockOnePass()
        for entry in MOCK_ENTRIES:
            for query in entry['queries']:
                self.assertEqual(json.dumps(entry['output']), op.get_raw(query))

    def test_onepassword_get_not_found(self):
        op = MockOnePass()
        self.assertEqual('', op.get_field('a fake query', 'a fake field'))

    def test_onepassword_get_with_section(self):
        op = MockOnePass()
        dummy, query, section_title, field_name, field_value = get_one_mock_query()
        self.assertEqual(field_value, op.get_field(query, field_name, section=section_title))

    def test_onepassword_get_with_vault(self):
        op = MockOnePass()
        entry, query, dummy, field_name, field_value = get_one_mock_query()
        for vault_query in [entry['vault_name'], entry['output']['vaultUuid']]:
            self.assertEqual(field_value, op.get_field(query, field_name, vault=vault_query))

    def test_onepassword_get_with_wrong_vault(self):
        op = MockOnePass()
        dummy, query, dummy, field_name, dummy = get_one_mock_query()
        self.assertEqual('', op.get_field(query, field_name, vault='a fake vault'))

    def test_onepassword_get_diff_case(self):
        op = MockOnePass()
        entry, query, section_title, field_name, field_value = get_one_mock_query()
        self.assertEqual(
            field_value,
            op.get_field(
                query,
                field_name.upper(),
                vault=entry['vault_name'].upper(),
                section=section_title.upper()
            )
        )


@patch('ansible.plugins.lookup.onepassword.OnePass', MockOnePass)
class TestLookupModule(unittest.TestCase):

    def test_onepassword_plugin_multiple(self):
        lookup_plugin = LookupModule()

        entry = MOCK_ENTRIES[0]
        field = entry['output']['details']['sections'][0]['fields'][0]

        self.assertEqual(
            [field['v']] * len(entry['queries']),
            lookup_plugin.run(entry['queries'], field=field['t'])
        )

    def test_onepassword_plugin_default_field(self):
        lookup_plugin = LookupModule()

        dummy, query, dummy, dummy, field_value = get_one_mock_query('password')
        self.assertEqual([field_value], lookup_plugin.run([query]))


@patch('ansible.plugins.lookup.onepassword_raw.OnePass', MockOnePass)
class TestOnePasswordRawLookup(unittest.TestCase):

    def test_onepassword_raw_plugin_multiple(self):
        raw_lookup_plugin = OnePasswordRawLookup()

        entry = MOCK_ENTRIES[0]
        raw_value = entry['output']

        self.assertEqual(
            [raw_value] * len(entry['queries']),
            raw_lookup_plugin.run(entry['queries'])
        )
