# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest
import random
import string
import sys
import unittest

from ansible import constants as C
from ansible.cli.arguments import option_helpers as opt_help
from ansible import __path__ as ansible_path
from ansible.release import __version__ as ansible_version

cpath = C.DEFAULT_MODULE_PATH
FAKE_PROG = u'ansible-cli-test'


@pytest.mark.parametrize(
    'must_have', [
        FAKE_PROG + u' [core %s]' % ansible_version,
        u'config file = %s' % C.CONFIG_FILE,
        u'configured module search path = %s' % cpath,
        u'ansible python module location = %s' % ':'.join(ansible_path),
        u'ansible collection location = %s' % ':'.join(C.COLLECTIONS_PATHS),
        u'executable location = ',
        u'python version = %s' % ''.join(sys.version.splitlines()),
    ]
)
def test_option_helper_version(must_have):
    version_output = opt_help.version(prog=FAKE_PROG)
    assert must_have in version_output


class TestHelperFunctions(unittest.TestCase):

    def setUp(self):

        # set some known and random 'good strings'
        self.good_strings = ['no bad chars', 'らとみ', 'café']
        source = string.ascii_lowercase + string.ascii_uppercase + string.digits + string.punctuation
        while len(self.good_strings) < 10:
            rand = ''.join(random.choices(source, k=random.randrange(1, 32)))
            if 'F' in rand or ';' in rand or '-' in rand:
                continue  # we only want 'GOOD' strings, also - removed as it is for flags
            self.good_strings.append(rand)

        # known 'bad' strings
        self.bad_strings = ['I have F', 'i ;', 'both ; and F', 'らとみ with F', ';café;']

        def _dont_exit(self, message=''):
            '''
                Avoid systemexit on argument parsing errors
                but now we have to check vars(namespace) for
                'non results'
            '''
            if message:
                print(message)

        self.p = opt_help.create_base_parser(prog=FAKE_PROG)
        self.p.error = _dont_exit
        self.p.add_argument('--test', dest='bogus', action='store', help='test arg',
                            type=opt_help.str_sans_forbidden_characters('F', ';'))

    def test_str_sans_forbidden_characters_detection(self):

        for good in self.good_strings:
            # bogus should be set to good arg
            parsed = self.p.parse_args(['--test', good])
            self.assertEqual(vars(parsed).get('bogus'), good)

        for bad in self.bad_strings:
            # bogus will not get set
            parsed = self.p.parse_args(['--test', bad])
            self.assertIsNone(vars(parsed).get('bogus'))

    def test_str_sans_forbidden_characters_input(self):

        for invalid in (True, 13, 6.2832, None):
            self.p.add_argument('--bad', dest='bogus', action='store',
                                type=opt_help.str_sans_forbidden_characters(invalid),
                                help='bad test arg')
            parsed = self.p.parse_args(['--bad', 'safe value'])
            self.assertIsNone(vars(parsed).get('bogus'))
