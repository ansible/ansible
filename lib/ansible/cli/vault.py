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
from ansible.parsing.vault import VaultEditor
from ansible.cli import CLI
from ansible.utils.display import Display
from ansible.utils.vault import read_vault_file

class VaultCLI(CLI):
    """ Vault command line class """

    VALID_ACTIONS = ("create", "decrypt", "edit", "encrypt", "rekey", "view")
    CIPHER = 'AES256'

    def __init__(self, args, display=None):

        self.vault_pass = None
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
        elif action == "rekey":
            self.parser.set_usage("usage: %prog rekey [options] file_name")

        self.options, self.args = self.parser.parse_args()
        self.display.verbosity = self.options.verbosity

        if len(self.args) == 0 or len(self.args) > 1:
            raise AnsibleOptionsError("Vault requires a single filename as a parameter")

    def run(self):

        if self.options.vault_password_file:
            # read vault_pass from a file
            self.vault_pass = read_vault_file(self.options.vault_password_file)
        elif self.options.ask_vault_pass:
            self.vault_pass, _= self.ask_vault_passwords(ask_vault_pass=True, ask_new_vault_pass=False, confirm_new=False)

        self.execute()

    def execute_create(self):

        cipher = getattr(self.options, 'cipher', self.CIPHER)
        this_editor = VaultEditor(cipher, self.vault_pass, self.args[0])
        this_editor.create_file()

    def execute_decrypt(self):

        cipher = getattr(self.options, 'cipher', self.CIPHER)
        for f in self.args:
            this_editor = VaultEditor(cipher, self.vault_pass, f)
            this_editor.decrypt_file()

        self.display.display("Decryption successful")

    def execute_edit(self):

        for f in self.args:
            this_editor = VaultEditor(None, self.vault_pass, f)
            this_editor.edit_file()

    def execute_view(self):

        for f in self.args:
            this_editor = VaultEditor(None, self.vault_pass, f)
            this_editor.view_file()

    def execute_encrypt(self):

        cipher = getattr(self.options, 'cipher', self.CIPHER)
        for f in self.args:
            this_editor = VaultEditor(cipher, self.vault_pass, f)
            this_editor.encrypt_file()

        self.display.display("Encryption successful")

    def execute_rekey(self):
        __, new_password = self.ask_vault_passwords(ask_vault_pass=False, ask_new_vault_pass=True, confirm_new=True)

        for f in self.args:
            this_editor = VaultEditor(None, self.vault_pass, f)
            this_editor.rekey_file(new_password)

        self.display.display("Rekey successful")
