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
from ansible.cli import CLI
#from ansible.utils import module_docs

class DocCLI(CLI):
    """ Vault command line class """

    BLACKLIST_EXTS = ('.pyc', '.swp', '.bak', '~', '.rpm')
    IGNORE_FILES = [ "COPYING", "CONTRIBUTING", "LICENSE", "README", "VERSION"]

    _ITALIC = re.compile(r"I\(([^)]+)\)")
    _BOLD   = re.compile(r"B\(([^)]+)\)")
    _MODULE = re.compile(r"M\(([^)]+)\)")
    _URL    = re.compile(r"U\(([^)]+)\)")
    _CONST  = re.compile(r"C\(([^)]+)\)")

    PAGER   = 'less'
    LESS_OPTS = 'FRSX'  # -F (quit-if-one-screen) -R (allow raw ansi control chars)
                        # -S (chop long lines) -X (disable termcap init and de-init)


    def parse(self):

        self.parser = optparse.OptionParser(
            version=version("%prog"),
            usage='usage: %prog [options] [module...]',
            description='Show Ansible module documentation',
        )

        self.parser.add_option("-M", "--module-path", action="store", dest="module_path", default=C.DEFAULT_MODULE_PATH,
                help="Ansible modules/ directory")
        self.parser.add_option("-l", "--list", action="store_true", default=False, dest='list_dir',
                help='List available modules')
        self.parser.add_option("-s", "--snippet", action="store_true", default=False, dest='show_snippet',
                help='Show playbook snippet for specified module(s)')
        self.parser.add_option('-v', action='version', help='Show version number and exit')


        self.options, self.args = self.parser.parse_args()
        self.display.verbosity = self.options.verbosity


    def run(self):

        if options.module_path is not None:
            for i in options.module_path.split(os.pathsep):
                utils.plugins.module_finder.add_directory(i)

        if options.list_dir:
            # list modules
            paths = utils.plugins.module_finder._get_paths()
            module_list = []
            for path in paths:
                find_modules(path, module_list)

            pager(get_module_list_text(module_list))

        if len(args) == 0:
            raise AnsibleOptionsError("Incorrect options passed")

