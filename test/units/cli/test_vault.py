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

from units.compat import unittest
from units.compat.mock import patch
from units.mock.vault_helper import TextVaultSecret

from ansible import errors
from ansible.cli.vault import VaultCLI


# TODO: make these tests assert something, likely by verifing
#       mock calls


class TestVaultCli(unittest.TestCase):
    def setUp(self):
        self.tty_patcher = patch('ansible.cli.sys.stdin.isatty', return_value=False)
        self.mock_isatty = self.tty_patcher.start()

    def tearDown(self):
        self.tty_patcher.stop()

    def test_parse_empty(self):
        cli = VaultCLI([])
        self.assertRaisesRegexp(errors.AnsibleOptionsError,
                                '.*Missing required action.*',
                                cli.parse)

    # FIXME: something weird seems to be afoot when parsing actions
    # cli = VaultCLI(args=['view', '/dev/null/foo', 'mysecret3'])
    # will skip '/dev/null/foo'. something in cli.CLI.set_action() ?
    #   maybe we self.args gets modified in a loop?
    def test_parse_view_file(self):
        cli = VaultCLI(args=['ansible-vault', 'view', '/dev/null/foo'])
        cli.parse()

    @patch('ansible.cli.vault.VaultCLI.setup_vault_secrets')
    def test_view_missing_file_no_secret(self, mock_setup_vault_secrets):
        mock_setup_vault_secrets.return_value = []
        cli = VaultCLI(args=['ansible-vault', 'view', '/dev/null/foo'])
        cli.parse()
        self.assertRaisesRegexp(errors.AnsibleOptionsError,
                                "A vault password is required to use Ansible's Vault",
                                cli.run)

    @patch('ansible.cli.vault.VaultCLI.setup_vault_secrets')
    def test_encrypt_missing_file_no_secret(self, mock_setup_vault_secrets):
        mock_setup_vault_secrets.return_value = []
        cli = VaultCLI(args=['ansible-vault', 'encrypt', '/dev/null/foo'])
        cli.parse()
        self.assertRaisesRegexp(errors.AnsibleOptionsError,
                                "A vault password is required to use Ansible's Vault",
                                cli.run)

    @patch('ansible.cli.vault.VaultCLI.setup_vault_secrets')
    @patch('ansible.cli.vault.VaultEditor')
    def test_encrypt(self, mock_vault_editor, mock_setup_vault_secrets):
        mock_setup_vault_secrets.return_value = [('default', TextVaultSecret('password'))]
        cli = VaultCLI(args=['ansible-vault', 'encrypt', '/dev/null/foo'])
        cli.parse()
        cli.run()

    @patch('ansible.cli.vault.VaultCLI.setup_vault_secrets')
    @patch('ansible.cli.vault.VaultEditor')
    def test_encrypt_string(self, mock_vault_editor, mock_setup_vault_secrets):
        mock_setup_vault_secrets.return_value = [('default', TextVaultSecret('password'))]
        cli = VaultCLI(args=['ansible-vault', 'encrypt_string',
                             'some string to encrypt'])
        cli.parse()
        cli.run()

    @patch('ansible.cli.vault.VaultCLI.setup_vault_secrets')
    @patch('ansible.cli.vault.VaultEditor')
    @patch('ansible.cli.vault.display.prompt', return_value='a_prompt')
    def test_encrypt_string_prompt(self, mock_display, mock_vault_editor, mock_setup_vault_secrets):
        mock_setup_vault_secrets.return_value = [('default', TextVaultSecret('password'))]
        cli = VaultCLI(args=['ansible-vault',
                             'encrypt_string',
                             '--prompt',
                             'some string to encrypt'])
        cli.parse()
        cli.run()

    @patch('ansible.cli.vault.VaultCLI.setup_vault_secrets')
    @patch('ansible.cli.vault.VaultEditor')
    @patch('ansible.cli.vault.sys.stdin.read', return_value='This is data from stdin')
    def test_encrypt_string_stdin(self, mock_stdin_read, mock_vault_editor, mock_setup_vault_secrets):
        mock_setup_vault_secrets.return_value = [('default', TextVaultSecret('password'))]
        cli = VaultCLI(args=['ansible-vault',
                             'encrypt_string',
                             '--stdin-name',
                             'the_var_from_stdin',
                             '-'])
        cli.parse()
        cli.run()

    @patch('ansible.cli.vault.VaultCLI.setup_vault_secrets')
    @patch('ansible.cli.vault.VaultEditor')
    def test_encrypt_string_names(self, mock_vault_editor, mock_setup_vault_secrets):
        mock_setup_vault_secrets.return_value = [('default', TextVaultSecret('password'))]
        cli = VaultCLI(args=['ansible-vault', 'encrypt_string',
                             '--name', 'foo1',
                             '--name', 'foo2',
                             'some string to encrypt'])
        cli.parse()
        cli.run()

    @patch('ansible.cli.vault.VaultCLI.setup_vault_secrets')
    @patch('ansible.cli.vault.VaultEditor')
    def test_encrypt_string_more_args_than_names(self, mock_vault_editor, mock_setup_vault_secrets):
        mock_setup_vault_secrets.return_value = [('default', TextVaultSecret('password'))]
        cli = VaultCLI(args=['ansible-vault', 'encrypt_string',
                             '--name', 'foo1',
                             'some string to encrypt',
                             'other strings',
                             'a few more string args'])
        cli.parse()
        cli.run()

    @patch('ansible.cli.vault.VaultCLI.setup_vault_secrets')
    @patch('ansible.cli.vault.VaultEditor')
    def test_create(self, mock_vault_editor, mock_setup_vault_secrets):
        mock_setup_vault_secrets.return_value = [('default', TextVaultSecret('password'))]
        cli = VaultCLI(args=['ansible-vault', 'create', '/dev/null/foo'])
        cli.parse()
        cli.run()

    @patch('ansible.cli.vault.VaultCLI.setup_vault_secrets')
    @patch('ansible.cli.vault.VaultEditor')
    def test_edit(self, mock_vault_editor, mock_setup_vault_secrets):
        mock_setup_vault_secrets.return_value = [('default', TextVaultSecret('password'))]
        cli = VaultCLI(args=['ansible-vault', 'edit', '/dev/null/foo'])
        cli.parse()
        cli.run()

    @patch('ansible.cli.vault.VaultCLI.setup_vault_secrets')
    @patch('ansible.cli.vault.VaultEditor')
    def test_decrypt(self, mock_vault_editor, mock_setup_vault_secrets):
        mock_setup_vault_secrets.return_value = [('default', TextVaultSecret('password'))]
        cli = VaultCLI(args=['ansible-vault', 'decrypt', '/dev/null/foo'])
        cli.parse()
        cli.run()

    @patch('ansible.cli.vault.VaultCLI.setup_vault_secrets')
    @patch('ansible.cli.vault.VaultEditor')
    def test_view(self, mock_vault_editor, mock_setup_vault_secrets):
        mock_setup_vault_secrets.return_value = [('default', TextVaultSecret('password'))]
        cli = VaultCLI(args=['ansible-vault', 'view', '/dev/null/foo'])
        cli.parse()
        cli.run()

    @patch('ansible.cli.vault.VaultCLI.setup_vault_secrets')
    @patch('ansible.cli.vault.VaultEditor')
    def test_rekey(self, mock_vault_editor, mock_setup_vault_secrets):
        mock_setup_vault_secrets.return_value = [('default', TextVaultSecret('password'))]
        cli = VaultCLI(args=['ansible-vault', 'rekey', '/dev/null/foo'])
        cli.parse()
        cli.run()
