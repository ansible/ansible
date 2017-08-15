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
    def setUp(self):
        self.fake_loader = DictDataLoader({})

    def test(self):
        res = cli.CLI.setup_vault_secrets(None, None)
        self.assertIsInstance(res, list)

    @patch('ansible.cli.get_file_vault_secret')
    def test_password_file(self, mock_file_secret):
        filename = '/dev/null/secret'
        mock_file_secret.return_value = MagicMock(bytes=b'file1_password',
                                                  vault_id='file1',
                                                  filename=filename)
        res = cli.CLI.setup_vault_secrets(loader=self.fake_loader,
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

        res = cli.CLI.setup_vault_secrets(loader=self.fake_loader,
                                          vault_ids=['prompt1@prompt'],
                                          ask_vault_pass=True)

        self.assertIsInstance(res, list)
        matches = vault.match_secrets(res, ['prompt1'])
        self.assertIn('prompt1', [x[0] for x in matches])
        match = matches[0][1]
        self.assertEqual(match.bytes, b'prompt1_password')

    def _assert_ids(self, vault_id_names, res, password=b'prompt1_password'):
        self.assertIsInstance(res, list)
        len_ids = len(vault_id_names)
        matches = vault.match_secrets(res, vault_id_names)
        self.assertEqual(len(res), len_ids)
        self.assertEqual(len(matches), len_ids)
        for index, prompt in enumerate(vault_id_names):
            self.assertIn(prompt, [x[0] for x in matches])
            # simple mock, same password/prompt for each mock_prompt_secret
            self.assertEqual(matches[index][1].bytes, password)

    @patch('ansible.cli.PromptVaultSecret')
    def test_multiple_prompts(self, mock_prompt_secret):
        mock_prompt_secret.return_value = MagicMock(bytes=b'prompt1_password',
                                                    vault_id='prompt1')

        res = cli.CLI.setup_vault_secrets(loader=self.fake_loader,
                                          vault_ids=['prompt1@prompt',
                                                     'prompt2@prompt'],
                                          ask_vault_pass=False)

        vault_id_names = ['prompt1', 'prompt2']
        self._assert_ids(vault_id_names, res)

    @patch('ansible.cli.PromptVaultSecret')
    def test_multiple_prompts_and_ask_vault_pass(self, mock_prompt_secret):
        mock_prompt_secret.return_value = MagicMock(bytes=b'prompt1_password',
                                                    vault_id='prompt1')

        res = cli.CLI.setup_vault_secrets(loader=self.fake_loader,
                                          vault_ids=['prompt1@prompt',
                                                     'prompt2@prompt',
                                                     'prompt3@prompt_ask_vault_pass'],
                                          ask_vault_pass=True)

        vault_id_names = ['prompt1', 'prompt2', 'prompt3', 'default']
        self._assert_ids(vault_id_names, res)

    @patch('ansible.cli.C')
    @patch('ansible.cli.get_file_vault_secret')
    @patch('ansible.cli.PromptVaultSecret')
    def test_default_file_vault(self, mock_prompt_secret,
                                mock_file_secret,
                                mock_config):
        mock_prompt_secret.return_value = MagicMock(bytes=b'prompt1_password',
                                                    vault_id='default')
        mock_file_secret.return_value = MagicMock(bytes=b'file1_password',
                                                  vault_id='default')
        mock_config.DEFAULT_VAULT_PASSWORD_FILE = '/dev/null/faux/vault_password_file'
        mock_config.DEFAULT_VAULT_IDENTITY = 'default'

        res = cli.CLI.setup_vault_secrets(loader=self.fake_loader,
                                          vault_ids=[],
                                          create_new_password=False,
                                          ask_vault_pass=True)

        self.assertIsInstance(res, list)
        matches = vault.match_secrets(res, ['default'])
        # --vault-password-file/DEFAULT_VAULT_PASSWORD_FILE is higher precendce than prompts
        # if the same vault-id ('default') regardless of cli order since it didn't matter in 2.3
        self.assertEqual(matches[0][1].bytes, b'file1_password')
        self.assertEqual(matches[1][1].bytes, b'prompt1_password')

    @patch('ansible.cli.get_file_vault_secret')
    @patch('ansible.cli.PromptVaultSecret')
    def test_default_file_vault_identity_list(self, mock_prompt_secret,
                                              mock_file_secret):
        default_vault_ids = ['some_prompt@prompt',
                             'some_file@/dev/null/secret']

        mock_prompt_secret.return_value = MagicMock(bytes=b'some_prompt_password',
                                                    vault_id='some_prompt')

        filename = '/dev/null/secret'
        mock_file_secret.return_value = MagicMock(bytes=b'some_file_password',
                                                  vault_id='some_file',
                                                  filename=filename)

        vault_ids = default_vault_ids
        res = cli.CLI.setup_vault_secrets(loader=self.fake_loader,
                                          vault_ids=vault_ids,
                                          create_new_password=False,
                                          ask_vault_pass=True)

        self.assertIsInstance(res, list)
        matches = vault.match_secrets(res, ['some_file'])
        # --vault-password-file/DEFAULT_VAULT_PASSWORD_FILE is higher precendce than prompts
        # if the same vault-id ('default') regardless of cli order since it didn't matter in 2.3
        self.assertEqual(matches[0][1].bytes, b'some_file_password')
        matches = vault.match_secrets(res, ['some_prompt'])
        self.assertEqual(matches[0][1].bytes, b'some_prompt_password')

    @patch('ansible.cli.PromptVaultSecret')
    def test_prompt_just_ask_vault_pass(self, mock_prompt_secret):
        mock_prompt_secret.return_value = MagicMock(bytes=b'prompt1_password',
                                                    vault_id='default')

        res = cli.CLI.setup_vault_secrets(loader=self.fake_loader,
                                          vault_ids=[],
                                          create_new_password=False,
                                          ask_vault_pass=True)

        self.assertIsInstance(res, list)
        match = vault.match_secrets(res, ['default'])[0][1]
        self.assertEqual(match.bytes, b'prompt1_password')

    @patch('ansible.cli.PromptVaultSecret')
    def test_prompt_new_password_ask_vault_pass(self, mock_prompt_secret):
        mock_prompt_secret.return_value = MagicMock(bytes=b'prompt1_password',
                                                    vault_id='default')

        res = cli.CLI.setup_vault_secrets(loader=self.fake_loader,
                                          vault_ids=[],
                                          create_new_password=True,
                                          ask_vault_pass=True)

        self.assertIsInstance(res, list)
        match = vault.match_secrets(res, ['default'])[0][1]
        self.assertEqual(match.bytes, b'prompt1_password')

    @patch('ansible.cli.PromptVaultSecret')
    def test_prompt_new_password_vault_id_prompt(self, mock_prompt_secret):
        mock_prompt_secret.return_value = MagicMock(bytes=b'prompt1_password',
                                                    vault_id='some_vault_id')

        res = cli.CLI.setup_vault_secrets(loader=self.fake_loader,
                                          vault_ids=['some_vault_id@prompt'],
                                          create_new_password=True,
                                          ask_vault_pass=False)

        self.assertIsInstance(res, list)
        match = vault.match_secrets(res, ['some_vault_id'])[0][1]
        self.assertEqual(match.bytes, b'prompt1_password')

    @patch('ansible.cli.PromptVaultSecret')
    def test_prompt_new_password_vault_id_prompt_ask_vault_pass(self, mock_prompt_secret):
        mock_prompt_secret.return_value = MagicMock(bytes=b'prompt1_password',
                                                    vault_id='default')

        res = cli.CLI.setup_vault_secrets(loader=self.fake_loader,
                                          vault_ids=['some_vault_id@prompt_ask_vault_pass'],
                                          create_new_password=True,
                                          ask_vault_pass=False)

        self.assertIsInstance(res, list)
        match = vault.match_secrets(res, ['some_vault_id'])[0][1]
        self.assertEqual(match.bytes, b'prompt1_password')

    @patch('ansible.cli.PromptVaultSecret')
    def test_prompt_new_password_vault_id_prompt_ask_vault_pass_ask_vault_pass(self, mock_prompt_secret):
        mock_prompt_secret.return_value = MagicMock(bytes=b'prompt1_password',
                                                    vault_id='default')

        res = cli.CLI.setup_vault_secrets(loader=self.fake_loader,
                                          vault_ids=['some_vault_id@prompt_ask_vault_pass'],
                                          create_new_password=True,
                                          ask_vault_pass=True)

        self.assertIsInstance(res, list)
        match = vault.match_secrets(res, ['some_vault_id'])[0][1]
        self.assertEqual(match.bytes, b'prompt1_password')
