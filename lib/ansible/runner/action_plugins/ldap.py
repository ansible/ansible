# -*- coding: utf-8 -*-
# (c) 2014, Jakub Jirutka <jakub@jirutka.cz>
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

from ansible import utils
from ansible.utils import template

## fixes https://github.com/ansible/ansible/issues/3518
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import pipes


class ActionModule(object):

    TRANSFERS_FILES = True

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):
        ''' Handler for file load and template operations. '''

        options = self._load_options(module_args, complex_args)
        source = options.get('src', None)

        if source:
            if source.endswith('.j2'):
                filepath = self._resolve_file_path(source, 'templates', inject)
                content = template.template_from_file(self.runner.basedir,
                        filepath, inject, vault_password=self.runner.vault_pass)
            else:
                filepath = self._resolve_file_path(source, 'files', inject)
                with open(filepath, 'r') as f:
                    content = f.read()

            module_args = "%s content=%s" % (module_args, pipes.quote(content))

        # propagate checkmode to module
        if self.runner.noop_on_check(inject):
            module_args += " CHECKMODE=True"

        return self.runner._execute_module(conn, tmp, 'ldap', module_args,
                inject=inject, complex_args=complex_args)

    def _load_options(self, module_args, complex_args):
        ''' Load module options. '''

        options = {}
        if complex_args:
            options.update(complex_args)
        options.update(utils.parse_kv(module_args))

        return options

    def _resolve_file_path(self, filepath, dirname, inject):
        ''' Resolve absolute path of the file. '''

        basedir = self.runner.basedir
        filepath = template.template(basedir, filepath, inject)

        if '_original_file' in inject:
            origin_path = inject['_original_file']
            filepath = utils.path_dwim_relative(origin_path, dirname, filepath, basedir)
        else:
            filepath = utils.path_dwim(basedir, filepath)

        return filepath
