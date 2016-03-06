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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import datetime
import os
import traceback
import textwrap

from ansible.compat.six import iteritems

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.plugins import module_loader
from ansible.cli import CLI
from ansible.utils import module_docs

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class DocCLI(CLI):
    """ Vault command line class """

    def __init__(self, args):

        super(DocCLI, self).__init__(args)
        self.module_list = []

    def parse(self):

        self.parser = CLI.base_parser(
            usage='usage: %prog [options] [module...]',
            epilog='Show Ansible module documentation',
            module_opts=True,
        )

        self.parser.add_option("-l", "--list", action="store_true", default=False, dest='list_dir',
                help='List available modules')
        self.parser.add_option("-s", "--snippet", action="store_true", default=False, dest='show_snippet',
                help='Show playbook snippet for specified module(s)')

        self.options, self.args = self.parser.parse_args(self.args[1:])
        display.verbosity = self.options.verbosity

    def run(self):

        super(DocCLI, self).run()

        if self.options.module_path is not None:
            for i in self.options.module_path.split(os.pathsep):
                module_loader.add_directory(i)

        # list modules
        if self.options.list_dir:
            paths = module_loader._get_paths()
            for path in paths:
                self.find_modules(path)

            self.pager(self.get_module_list_text())
            return 0

        if len(self.args) == 0:
            raise AnsibleOptionsError("Incorrect options passed")

        # process command line module list
        text = ''
        for module in self.args:

            try:
                # if the module lives in a non-python file (eg, win_X.ps1), require the corresponding python file for docs
                filename = module_loader.find_plugin(module, mod_type='.py')
                if filename is None:
                    display.warning("module %s not found in %s\n" % (module, DocCLI.print_paths(module_loader)))
                    continue

                if any(filename.endswith(x) for x in C.BLACKLIST_EXTS):
                    continue

                try:
                    doc, plainexamples, returndocs = module_docs.get_docstring(filename, verbose=(self.options.verbosity > 0))
                except:
                    display.vvv(traceback.print_exc())
                    display.error("module %s has a documentation error formatting or is missing documentation\nTo see exact traceback use -vvv" % module)
                    continue

                if doc is not None:

                    all_keys = []
                    for (k,v) in iteritems(doc['options']):
                        all_keys.append(k)
                    all_keys = sorted(all_keys)
                    doc['option_keys'] = all_keys

                    doc['filename']         = filename
                    doc['docuri']           = doc['module'].replace('_', '-')
                    doc['now_date']         = datetime.date.today().strftime('%Y-%m-%d')
                    doc['plainexamples']    = plainexamples
                    doc['returndocs']       = returndocs

                    if self.options.show_snippet:
                        text += self.get_snippet_text(doc)
                    else:
                        text += self.get_man_text(doc)
                else:
                    # this typically means we couldn't even parse the docstring, not just that the YAML is busted,
                    # probably a quoting issue.
                    raise AnsibleError("Parsing produced an empty object.")
            except Exception as e:
                display.vvv(traceback.print_exc())
                raise AnsibleError("module %s missing documentation (or could not parse documentation): %s\n" % (module, str(e)))

        self.pager(text)
        return 0

    def find_modules(self, path):

        if os.path.isdir(path):
            for module in os.listdir(path):
                if module.startswith('.'):
                    continue
                elif os.path.isdir(module):
                    self.find_modules(module)
                elif any(module.endswith(x) for x in C.BLACKLIST_EXTS):
                    continue
                elif module.startswith('__'):
                    continue
                elif module in C.IGNORE_FILES:
                    continue
                elif module.startswith('_'):
                    fullpath = '/'.join([path,module])
                    if os.path.islink(fullpath): # avoids aliases
                        continue

                module = os.path.splitext(module)[0] # removes the extension
                self.module_list.append(module)

    def get_module_list_text(self):
        columns = display.columns
        displace = max(len(x) for x in self.module_list)
        linelimit = columns - displace - 5
        text = []
        deprecated = []
        for module in sorted(set(self.module_list)):

            if module in module_docs.BLACKLIST_MODULES:
                continue

            # if the module lives in a non-python file (eg, win_X.ps1), require the corresponding python file for docs
            filename = module_loader.find_plugin(module, mod_type='.py')

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
                raise AnsibleError("module %s has a documentation error formatting or is missing documentation\n" % module)

        if len(deprecated) > 0:
            text.append("\nDEPRECATED:")
            text.extend(deprecated)
        return "\n".join(text)

    @staticmethod
    def print_paths(finder):
        ''' Returns a string suitable for printing of the search path '''

        # Uses a list to get the order right
        ret = []
        for i in finder._get_paths():
            if i not in ret:
                ret.append(i)
        return os.pathsep.join(ret)

    def get_snippet_text(self, doc):

        text = []
        desc = CLI.tty_ify(doc['short_description'])
        text.append("- name: %s" % (desc))
        text.append("  action: %s" % (doc['module']))
        pad = 31
        subdent = ''.join([" " for a in xrange(pad)])
        limit = display.columns - pad

        for o in sorted(doc['options'].keys()):
            opt = doc['options'][o]
            desc = CLI.tty_ify(" ".join(opt['description']))

            if opt.get('required', False):
                s = o + "="
            else:
                s = o
            text.append("      %-20s   # %s" % (s, textwrap.fill(desc, limit, subsequent_indent=subdent)))
        text.append('')

        return "\n".join(text)

    def get_man_text(self, doc):

        opt_indent="        "
        text = []
        text.append("> %s\n" % doc['module'].upper())
        pad = display.columns * 0.20
        limit = max(display.columns - int(pad), 70)

        if isinstance(doc['description'], list):
            desc = " ".join(doc['description'])
        else:
            desc = doc['description']

        text.append("%s\n" % textwrap.fill(CLI.tty_ify(desc), limit, initial_indent="  ", subsequent_indent="  "))

        if 'deprecated' in doc and doc['deprecated'] is not None and len(doc['deprecated']) > 0:
            text.append("DEPRECATED: \n%s\n" % doc['deprecated'])

        if 'option_keys' in doc and len(doc['option_keys']) > 0:
            text.append("Options (= is mandatory):\n")

        for o in sorted(doc['option_keys']):
            opt = doc['options'][o]

            if opt.get('required', False):
                opt_leadin = "="
            else:
                opt_leadin = "-"

            text.append("%s %s" % (opt_leadin, o))

            if isinstance(opt['description'], list):
                desc = " ".join(opt['description'])
            else:
                desc = opt['description']

            if 'choices' in opt:
                choices = ", ".join(str(i) for i in opt['choices'])
                desc = desc + " (Choices: " + choices + ")"
            if 'default' in opt:
                default = str(opt['default'])
                desc = desc + " [Default: " + default + "]"
            text.append("%s\n" % textwrap.fill(CLI.tty_ify(desc), limit, initial_indent=opt_indent, subsequent_indent=opt_indent))

        if 'notes' in doc and doc['notes'] and len(doc['notes']) > 0:
            notes = " ".join(doc['notes'])
            text.append("Notes:%s\n" % textwrap.fill(CLI.tty_ify(notes), limit-6, initial_indent="  ", subsequent_indent=opt_indent))

        if 'requirements' in doc and doc['requirements'] is not None and len(doc['requirements']) > 0:
            req = ", ".join(doc['requirements'])
            text.append("Requirements:%s\n" % textwrap.fill(CLI.tty_ify(req), limit-16, initial_indent="  ", subsequent_indent=opt_indent))

        if 'examples' in doc and len(doc['examples']) > 0:
            text.append("Example%s:\n" % ('' if len(doc['examples']) < 2 else 's'))
            for ex in doc['examples']:
                text.append("%s\n" % (ex['code']))

        if 'plainexamples' in doc and doc['plainexamples'] is not None:
            text.append("EXAMPLES:")
            text.append(doc['plainexamples'])
        if 'returndocs' in doc and doc['returndocs'] is not None:
            text.append("RETURN VALUES:")
            text.append(doc['returndocs'])
        text.append('')

        maintainers = set()
        if 'author' in doc:
            if isinstance(doc['author'], basestring):
                maintainers.add(doc['author'])
            else:
                maintainers.update(doc['author'])

        if 'maintainers' in doc:
            if isinstance(doc['maintainers'], basestring):
                maintainers.add(doc['author'])
            else:
                maintainers.update(doc['author'])

        text.append('MAINTAINERS: ' + ', '.join(maintainers))
        text.append('')

        return "\n".join(text)
