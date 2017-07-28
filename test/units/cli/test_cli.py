# (c) 2017, Adrian Likins <alikins@redhat.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock

from units.mock.loader import DictDataLoader

from ansible.release import __version__
from ansible.parsing import vault
from ansible import cli


class TestCliVersion(unittest.TestCase):

    def test_version(self):
        ver = cli.CLI.version('ansible-cli-test')
        self.assertIn('ansible-cli-test', ver)
        self.assertIn('python version', ver)

    def test_version_info(self):
        version_info = cli.CLI.version_info()
        self.assertEqual(version_info['string'], __version__)

    def test_version_info_gitinfo(self):
        version_info = cli.CLI.version_info(gitinfo=True)
        self.assertIn('python version', version_info['string'])


class TestCliSetupVaultSecrets(unittest.TestCase):
    def test(self):
        res = cli.CLI.setup_vault_secrets(None, None)
        self.assertIsInstance(res, list)

    @patch('ansible.cli.get_file_vault_secret')
    def test_password_file(self, mock_file_secret):
        filename = '/dev/null/secret'
        mock_file_secret.return_value = MagicMock(bytes=b'file1_password',
                                                  vault_id='file1',
                                                  filename=filename)
        fake_loader = DictDataLoader({})
        res = cli.CLI.setup_vault_secrets(loader=fake_loader,
                                          vault_ids=['secret1@%s' % filename, 'secret2'],
                                          vault_password_files=[filename])
        self.assertIsInstance(res, list)
        matches = vault.match_secrets(res, ['secret1'])
        self.assertIn('secret1', [x[0] for x in matches])
        match = matches[0][1]
        self.assertEqual(match.bytes, b'file1_password')

    @patch('ansible.cli.PromptVaultSecret')
    def test_prompt(self, mock_prompt_secret):
        mock_prompt_secret.return_value = MagicMock(bytes=b'prompt1_password',
                                                    vault_id='prompt1')

        fake_loader = DictDataLoader({})
        res = cli.CLI.setup_vault_secrets(loader=fake_loader,
                                          vault_ids=['prompt1@prompt'],
                                          ask_vault_pass=True)

        self.assertIsInstance(res, list)
        matches = vault.match_secrets(res, ['prompt1'])
        self.assertIn('prompt1', [x[0] for x in matches])
        # self.assertIn('prompt1', res)
        # self.assertIn('secret1', res)
        match = matches[0][1]
        self.assertEqual(match.bytes, b'prompt1_password')
