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

import fcntl
import os
import re
import struct
import sys
import termios
import traceback

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.plugins import module_loader
from ansible.cli import CLI
from ansible.utils import module_docs

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

    def __init__(self, args, display=None):

        super(DocCLI, self).__init__(args, display)
        self.module_list = []

    def parse(self):

        self.parser = CLI.base_parser(
            usage='usage: %prog [options] [module...]',
            epilog='Show Ansible module documentation',
        )

        self.parser.add_option("-M", "--module-path", action="store", dest="module_path", default=C.DEFAULT_MODULE_PATH,
                help="Ansible modules/ directory")
        self.parser.add_option("-l", "--list", action="store_true", default=False, dest='list_dir',
                help='List available modules')
        self.parser.add_option("-s", "--snippet", action="store_true", default=False, dest='show_snippet',
                help='Show playbook snippet for specified module(s)')

        self.options, self.args = self.parser.parse_args()
        self.display.verbosity = self.options.verbosity


    def run(self):

        if self.options.module_path is not None:
            for i in self.options.module_path.split(os.pathsep):
                module_loader.add_directory(i)

        if self.options.list_dir:
            # list modules
            paths = module_loader._get_paths()
            for path in paths:
                self.find_modules(path)

            #self.pager(get_module_list_text(module_list))
            print self.get_module_list_text()
            return 0

        if len(self.args) == 0:
            raise AnsibleOptionsError("Incorrect options passed")


    def find_modules(self, path):

        if os.path.isdir(path):
            for module in os.listdir(path):
                if module.startswith('.'):
                    continue
                elif os.path.isdir(module):
                    self.find_modules(module)
                elif any(module.endswith(x) for x in self.BLACKLIST_EXTS):
                    continue
                elif module.startswith('__'):
                    continue
                elif module in self.IGNORE_FILES:
                    continue
                elif module.startswith('_'):
                    fullpath = '/'.join([path,module])
                    if os.path.islink(fullpath): # avoids aliases
                        continue

                module = os.path.splitext(module)[0] # removes the extension
                self.module_list.append(module)


    def get_module_list_text(self):
        tty_size = 0
        if os.isatty(0):
            tty_size = struct.unpack('HHHH',
                fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0)))[1]
        columns = max(60, tty_size)
        displace = max(len(x) for x in self.module_list)
        linelimit = columns - displace - 5
        text = []
        deprecated = []
        for module in sorted(set(self.module_list)):

            if module in module_docs.BLACKLIST_MODULES:
                continue

            filename = module_loader.find_plugin(module)

            if filename is None:
                continue
            if filename.endswith(".ps1"):
                continue
            if os.path.isdir(filename):
                continue

            try:
                doc, plainexamples, returndocs = module_docs.get_docstring(filename)
                desc = self.tty_ify(doc.get('short_description', '?')).strip()
                if len(desc) > linelimit:
                    desc = desc[:linelimit] + '...'

                if module.startswith('_'): # Handle deprecated
                    deprecated.append("%-*s %-*.*s" % (displace, module[1:], linelimit, len(desc), desc))
                else:
                    text.append("%-*s %-*.*s" % (displace, module, linelimit, len(desc), desc))
            except:
                traceback.print_exc()
                sys.stderr.write("ERROR: module %s has a documentation error formatting or is missing documentation\n" % module)

        if len(deprecated) > 0:
            text.append("\nDEPRECATED:")
            text.extend(deprecated)
        return "\n".join(text)

    @classmethod
    def tty_ify(self, text):

        t = self._ITALIC.sub("`" + r"\1" + "'", text)    # I(word) => `word'
        t = self._BOLD.sub("*" + r"\1" + "*", t)         # B(word) => *word*
        t = self._MODULE.sub("[" + r"\1" + "]", t)       # M(word) => [word]
        t = self._URL.sub(r"\1", t)                      # U(word) => word
        t = self._CONST.sub("`" + r"\1" + "'", t)        # C(word) => `word'

        return t
