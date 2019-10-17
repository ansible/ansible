# -*- coding: utf-8 -*-
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

import os
import pytest

from units.compat import unittest
from units.compat.mock import patch, MagicMock
from units.mock.vault_helper import TextVaultSecret

from ansible import context, errors
from ansible.cli.vault import VaultCLI
from ansible.module_utils._text import to_text
from ansible.utils import context_objects as co


# TODO: make these tests assert something, likely by verifing
#       mock calls


@pytest.fixture(autouse='function')
def reset_cli_args():
    co.GlobalCLIArgs._Singleton__instance = None
    yield
    co.GlobalCLIArgs._Singleton__instance = None


class TestVaultCli(unittest.TestCase):
    def setUp(self):
        self.tty_patcher = patch('ansible.cli.sys.stdin.isatty', return_value=False)
        self.mock_isatty = self.tty_patcher.start()

    def tearDown(self):
        self.tty_patcher.stop()

    def test_parse_empty(self):
        cli = VaultCLI(['vaultcli'])
        self.assertRaises(SystemExit,
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


@pytest.mark.parametrize('cli_args, expected', [
    (['ansible-vault', 'view', 'vault.txt'], 0),
    (['ansible-vault', 'view', 'vault.txt', '-vvv'], 3),
    (['ansible-vault', '-vv', 'view', 'vault.txt'], 2),
    # Due to our manual parsing we want to verify that -v set in the sub parser takes precedence. This behaviour is
    # deprecated and tests should be removed when the code that handles it is removed
    (['ansible-vault', '-vv', 'view', 'vault.txt', '-v'], 1),
    (['ansible-vault', '-vv', 'view', 'vault.txt', '-vvvv'], 4),
])
def test_verbosity_arguments(cli_args, expected, tmp_path_factory, monkeypatch):
    # Add a password file so we don't get a prompt in the test
    test_dir = to_text(tmp_path_factory.mktemp('test-ansible-vault'))
    pass_file = os.path.join(test_dir, 'pass.txt')
    with open(pass_file, 'w') as pass_fd:
        pass_fd.write('password')

    cli_args.extend(['--vault-id', pass_file])

    # Mock out the functions so we don't actually execute anything
    for func_name in [f for f in dir(VaultCLI) if f.startswith("execute_")]:
        monkeypatch.setattr(VaultCLI, func_name, MagicMock())

    cli = VaultCLI(args=cli_args)
    cli.run()

    assert context.CLIARGS['verbosity'] == expected
