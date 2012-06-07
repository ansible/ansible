# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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

#############################################

from ansible import utils
from ansible import errors
from ansible.playbook.task import Task
import shlex
import os

class Play(object):

    __slots__ = [ 
       'hosts', 'name', 'vars', 'vars_prompt', 'vars_files', 'handlers', 'remote_user', 'remote_port',
       'sudo', 'sudo_user', 'transport', 'playbook', '_ds', '_handlers', '_tasks' 
    ]

    # *************************************************

    def __init__(self, playbook, ds):
        ''' constructor loads from a play datastructure '''

        # TODO: more error handling

        hosts = ds.get('hosts')
        if hosts is None:
            raise errors.AnsibleError('hosts declaration is required')
        elif isinstance(hosts, list):
            hosts = ';'.join(hosts)
        hosts = utils.template(hosts, playbook.extra_vars, {})

        self._ds         = ds
        self.playbook    = playbook
        self.hosts       = hosts 
        self.name        = ds.get('name', self.hosts)
        self.vars        = ds.get('vars', {})
        self.vars_files  = ds.get('vars_files', [])
        self.vars_prompt = ds.get('vars_prompt', {})
        self.vars        = self._get_vars(self.playbook.basedir)
        self._tasks      = ds.get('tasks', [])
        self._handlers   = ds.get('handlers', [])
        self.remote_user = ds.get('user', self.playbook.remote_user)
        self.remote_port = ds.get('port', self.playbook.remote_port)
        self.sudo        = ds.get('sudo', self.playbook.sudo)
        self.sudo_user   = ds.get('sudo_user', self.playbook.sudo_user)
        self.transport   = ds.get('connection', self.playbook.transport)
        self._tasks      = self._load_tasks(self._ds, 'tasks')
        self._handlers   = self._load_tasks(self._ds, 'handlers')

        if self.sudo_user != 'root':
            self.sudo = True

    # *************************************************

    def _load_tasks(self, ds, keyname):
        ''' handle task and handler include statements '''

        items = ds.get(keyname, [])
        results = []
        for x in items:
            if 'include' in x:
                task_vars = self.vars.copy() 
                tokens = shlex.split(x['include'])
                for t in tokens[1:]:
                    (k,v) = t.split("=", 1)
                    task_vars[k]=v
                include_file = tokens[0]
                data = utils.parse_yaml_from_file(utils.path_dwim(self.playbook.basedir, include_file))
                for y in data:
                    items = y.get('with_items',None)
                    if items is None:
                        items = [ '' ]
                    for item in items:
                        mv = self.vars.copy()
                        mv.update(task_vars)
                        mv['item'] = item
                        results.append(Task(self,y,module_vars=mv))
            elif type(x) == dict:
                items = x.get('with_items', None)
                if items is None:
                    items = [ '' ]
                for item in items:
                    mv = self.vars.copy()
                    mv['item'] = item
                    results.append(Task(self,x,module_vars=mv))
            else:
                raise Exception("unexpected task type")
        return results

    # *************************************************

    def tasks(self):
        ''' return task objects for this play '''
        return self._tasks      

    def handlers(self):
        ''' return handler objects for this play '''
        return self._handlers

    # *************************************************

    def _get_vars(self, dirname):
        ''' load the vars section from a play, accounting for all sorts of variable features
        including loading from yaml files, prompting, and conditional includes of the first
        file found in a list. '''

        if self.vars is None:
            self.vars = {}

        if type(self.vars) not in [dict, list]:
            raise errors.AnsibleError("'vars' section must contain only key/value pairs")

        vars = self.playbook.global_vars
    
        # translate a list of vars into a dict
        if type(self.vars) == list:
            for item in self.vars:
                k, v = item.items()[0]
                vars[k] = v
        else:
            vars.update(self.vars)

        if type(self.vars_prompt) != dict:
            raise errors.AnsibleError("'vars_prompt' section must contain only key/value pairs")
        for vname in self.vars_prompt:
            vars[vname] = self.playbook.callbacks.on_vars_prompt(vname)

        results = self.playbook.extra_vars.copy()
        results.update(vars)
        return results

    # *************************************************

    def update_vars_files(self, hosts):
        ''' calculate vars_files, which requires that setup runs first so ansible facts can be mixed in '''
        for h in hosts:
            self._update_vars_files_for_host(h)

    # *************************************************

    def _update_vars_files_for_host(self, host):

        if not host in self.playbook.SETUP_CACHE:
            # no need to process failed hosts or hosts not in this play
            return

        for filename in self.vars_files:

            if type(filename) == list:

                # loop over all filenames, loading the first one, and failing if # none found
                found = False
                sequence = []
                for real_filename in filename:
                    filename2 = utils.template(real_filename, self.playbook.SETUP_CACHE[host])
                    filename2 = utils.template(filename2, self.vars)
                    filename2 = utils.path_dwim(self.playbook.basedir, filename2)
                    sequence.append(filename2)
                    if os.path.exists(filename2):
                        found = True
                        data = utils.parse_yaml_from_file(filename2)
                        self.playbook.SETUP_CACHE[host].update(data)
                        self.playbook.callbacks.on_import_for_host(host, filename2)
                        break
                    else:
                        self.playbook.callbacks.on_not_import_for_host(host, filename2)
                if not found:
                    raise errors.AnsibleError(
                        "%s: FATAL, no files matched for vars_files import sequence: %s" % (host, sequence)
                    )

            else:

                filename2 = utils.template(filename, self.playbook.SETUP_CACHE[host])
                filename2 = utils.template(filename2, self.vars)
                fpath = utils.path_dwim(self.playbook.basedir, filename2)
                new_vars = utils.parse_yaml_from_file(fpath)
                if new_vars:
                    self.playbook.SETUP_CACHE[host].update(new_vars)
                #else: could warn if vars file contains no vars. 
