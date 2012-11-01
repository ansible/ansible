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

import ansible

from ansible.callbacks import vv
from ansible.errors import AnsibleError as ae
from ansible.runner.return_data import ReturnData
from ansible.utils import path_dwim, parse_kv

class ActionModule(object):
    ''' Define custom jinja2 template filters '''

    ### We need to be able to return function pointers
    BYPASS_HOST_LOOP = True

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject):
        args = parse_kv(self.runner.module_args)
        if not 'src' in args:
            raise ae("'src' is a required argument.")
        if not 'name' in args:
            raise ae("'name' is a required argument.")

        vv("created 'jinja2_filter' ActionModule: src=%s name=%s"%(args['src'],args['name']))

        module_path = path_dwim(self.runner.basedir, args['src'])

        if not os.path.exists(module_path):
            raise ae("'%s' does not exist."%(module_path))

        filters = inject.get('ansible_jinja2_filters',[])
        module = imp.load_source('module', module_path)
        for name in args['name'].strip(',').split(','):
            try:
                fn = getattr(module, name)
            except AttributeError:
                raise ae("Module '%s' has no filter '%s'"%(module_path, name))
            filters.append((name,fn))

        result = {'changed': False, 'ansible_facts': {'ansible_jinja2_filters': filters}}

        return ReturnData(conn=conn, comm_ok=True, result=result)
