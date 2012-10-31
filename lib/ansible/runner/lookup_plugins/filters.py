# Copyright 2012, Jeroen Hoekx <jeroen@hoekx.be>
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

import imp
import os

from ansible.errors import AnsibleError as ae
from ansible.utils import path_dwim, parse_kv, template

class LookupModule(object):

    def __init__(self, runner, **kwargs):
        self.runner = runner

    def run(self, terms, inject, **kwargs):
        filters = {}

        for term in terms:
            args = parse_kv(template(self.runner.basedir, term, inject))
            if not 'src' in args:
                raise ae("'src' is a required argument.")
            if not 'name' in args:
                raise ae("'name' is a required argument.")

            module_path = path_dwim(self.runner.basedir, args['src'])

            if not os.path.exists(module_path):
                raise ae("'%s' does not exist."%(module_path))

            module = imp.load_source('module', module_path)
            for name in args['name'].strip(',').split(','):
                try:
                    fn = getattr(module, name)
                except AttributeError:
                    raise ae("Module '%s' has no filter '%s'"%(module_path, name))
                filters[name] = fn

        return [{'ansible_jinja2_filters':filters}]
