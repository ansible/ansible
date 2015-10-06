# (c) 2014, James Tanner <tanner.jc@gmail.com>
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
#
# ansible-vault is a script that encrypts/decrypts YAML files. See
# http://docs.ansible.com/playbooks_vault.html for more details.

import os
import sys
import traceback

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.parsing import DataLoader
from ansible.parsing.vault import VaultEditor
from ansible.cli import CLI
from ansible.utils.display import Display

class VaultCLI(CLI):
    """ Vault command line class """

    VALID_ACTIONS = ("create", "decrypt", "edit", "encrypt", "rekey", "view")

    def __init__(self, args, display=None):

        self.vault_pass = None
        self.new_vault_pass = None
        super(VaultCLI, self).__init__(args, display)

    def parse(self):

        self.parser = CLI.base_parser(
            vault_opts=True,
            usage = "usage: %%prog [%s] [--help] [options] vaultfile.yml" % "|".join(self.VALID_ACTIONS),
            epilog = "\nSee '%s <command> --help' for more information on a specific command.\n\n" % os.path.basename(sys.argv[0])
        )

        self.set_action()

        # options specific to self.actions
        if self.action == "create":
            self.parser.set_usage("usage: %prog create [options] file_name")
        elif self.action == "decrypt":
            self.parser.set_usage("usage: %prog decrypt [options] file_name")
        elif self.action == "edit":
            self.parser.set_usage("usage: %prog edit [options] file_name")
        elif self.action == "view":
            self.parser.set_usage("usage: %prog view [options] file_name")
        elif self.action == "encrypt":
            self.parser.set_usage("usage: %prog encrypt [options] file_name")
        elif self.action == "rekey":
            self.parser.set_usage("usage: %prog rekey [options] file_name")

        self.options, self.args = self.parser.parse_args()
        self.display.verbosity = self.options.verbosity

        can_output = ['encrypt', 'decrypt']

        if self.action not in can_output:
            if self.options.output_file:
                raise AnsibleOptionsError("The --output option can be used only with ansible-vault %s" % '/'.join(can_output))
            if len(self.args) == 0:
                raise AnsibleOptionsError("Vault requires at least one filename as a parameter")
        else:
            # This restriction should remain in place until it's possible to
            # load multiple YAML records from a single file, or it's too easy
            # to create an encrypted file that can't be read back in. But in
            # the meanwhile, "cat a b c|ansible-vault encrypt --output x" is
            # a workaround.
            if self.options.output_file and len(self.args) > 1:
                raise AnsibleOptionsError("At most one input file may be used with the --output option")

    def run(self):

        super(VaultCLI, self).run()
        loader = DataLoader()

        if self.options.vault_password_file:
            # read vault_pass from a file
            self.vault_pass = CLI.read_vault_password_file(self.options.vault_password_file, loader)
        else:
            self.vault_pass, _= self.ask_vault_passwords(ask_vault_pass=True, ask_new_vault_pass=False, confirm_new=False)

        if self.options.new_vault_password_file:
            # for rekey only
            self.new_vault_pass = CLI.read_vault_password_file(self.options.new_vault_password_file, loader)

        if not self.vault_pass:
            raise AnsibleOptionsError("A password is required to use Ansible's Vault")

        self.editor = VaultEditor(self.vault_pass)

        self.execute()

    def execute_encrypt(self):

        if len(self.args) == 0 and sys.stdin.isatty():
            self.display.display("Reading plaintext input from stdin", stderr=True)

        for f in self.args or ['-']:
            self.editor.encrypt_file(f, output_file=self.options.output_file)

        if sys.stdout.isatty():
            self.display.display("Encryption successful", stderr=True)

    def execute_decrypt(self):

        if len(self.args) == 0 and sys.stdin.isatty():
            self.display.display("Reading ciphertext input from stdin", stderr=True)

        for f in self.args or ['-']:
            self.editor.decrypt_file(f, output_file=self.options.output_file)

        if sys.stdout.isatty():
            self.display.display("Decryption successful", stderr=True)

    def execute_create(self):

        if len(self.args) > 1:
            raise AnsibleOptionsError("ansible-vault create can take only one filename argument")

        self.editor.create_file(self.args[0])

    def execute_edit(self):
        for f in self.args:
            self.editor.edit_file(f)

    def execute_view(self):

        for f in self.args:
            self.pager(self.editor.plaintext(f))

    def execute_rekey(self):
        for f in self.args:
            if not (os.path.isfile(f)):
                raise AnsibleError(f + " does not exist")

        if self.new_vault_pass:
            new_password = self.new_vault_pass
        else:
            __, new_password = self.ask_vault_passwords(ask_vault_pass=False, ask_new_vault_pass=True, confirm_new=True)

        for f in self.args:
            self.editor.rekey_file(f, new_password)

        self.display.display("Rekey successful", stderr=True)
