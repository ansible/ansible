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
       'hosts', 'name', 'vars', 'vars_prompt', 'vars_files',
       'handlers', 'remote_user', 'remote_port',
       'sudo', 'sudo_user', 'transport', 'playbook',
       'tags', 'gather_facts', 'serial', '_ds', '_handlers', '_tasks',
       'basedir'
    ]

    # to catch typos and so forth -- these are userland names
    # and don't line up 1:1 with how they are stored
    VALID_KEYS = [
       'hosts', 'name', 'vars', 'vars_prompt', 'vars_files',
       'tasks', 'handlers', 'user', 'port', 'include',
       'sudo', 'sudo_user', 'connection', 'tags', 'gather_facts', 'serial'
    ]

    # *************************************************

    def __init__(self, playbook, ds, basedir):
        ''' constructor loads from a play datastructure '''

        for x in ds.keys():
            if not x in Play.VALID_KEYS:
                raise errors.AnsibleError("%s is not a legal parameter in an Ansible Playbook" % x)

        # TODO: more error handling

        hosts = ds.get('hosts')
        if hosts is None:
            raise errors.AnsibleError('hosts declaration is required')
        elif isinstance(hosts, list):
            hosts = ';'.join(hosts)
        hosts = utils.template(basedir, hosts, playbook.extra_vars)
        self._ds          = ds
        self.playbook     = playbook
        self.basedir      = basedir
        self.hosts        = hosts
        self.name         = ds.get('name', self.hosts)
        self.vars         = ds.get('vars', {})
        self.vars_files   = ds.get('vars_files', [])
        self.vars_prompt  = ds.get('vars_prompt', {})
        self.vars         = self._get_vars()
        self._tasks       = ds.get('tasks', [])
        self._handlers    = ds.get('handlers', [])
        self.remote_user  = utils.template(basedir, ds.get('user', self.playbook.remote_user), playbook.extra_vars)
        self.remote_port  = ds.get('port', self.playbook.remote_port)
        self.sudo         = ds.get('sudo', self.playbook.sudo)
        self.sudo_user    = ds.get('sudo_user', self.playbook.sudo_user)
        self.transport    = ds.get('connection', self.playbook.transport)
        self.tags         = ds.get('tags', None)
        self.gather_facts = ds.get('gather_facts', True)
        self.serial       = ds.get('serial', 0)

        self._update_vars_files_for_host(None)

        self._tasks      = self._load_tasks(self._ds, 'tasks')
        self._handlers   = self._load_tasks(self._ds, 'handlers')

        if self.tags is None:
            self.tags = []
        elif type(self.tags) in [ str, unicode ]:
            self.tags = [ self.tags ]
        elif type(self.tags) != list:
            self.tags = []

        if self.sudo_user != 'root':
            self.sudo = True

    # *************************************************

    def _load_tasks(self, ds, keyname):
        ''' handle task and handler include statements '''

        tasks = ds.get(keyname, [])
        results = []
        for x in tasks:
            task_vars = self.vars.copy()
            if 'include' in x:
                tokens = shlex.split(x['include'])
                for t in tokens[1:]:
                    (k,v) = t.split("=", 1)
                    task_vars[k] = utils.template(self.basedir, v, task_vars)
                include_file = utils.template(self.basedir, tokens[0], task_vars)
                data = utils.parse_yaml_from_file(utils.path_dwim(self.basedir, include_file))
            elif type(x) == dict:
                data = [x]
            else:
                raise Exception("unexpected task type")

            for y in data:
                mv = task_vars.copy()
                results.append(Task(self,y,module_vars=mv))

        for x in results:
            if self.tags is not None:
                x.tags.extend(self.tags)

        return results

    # *************************************************

    def tasks(self):
        ''' return task objects for this play '''
        return self._tasks

    def handlers(self):
        ''' return handler objects for this play '''
        return self._handlers

    # *************************************************

    def _get_vars(self):
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
                if getattr(item, 'items', None) is None:
                    raise errors.AnsibleError("expecting a key-value pair in 'vars' section")
                k, v = item.items()[0]
                vars[k] = v
        else:
            vars.update(self.vars)

        if type(self.vars_prompt) == list:
            for var in self.vars_prompt:
                if not 'name' in var:
                    raise errors.AnsibleError("'vars_prompt' item is missing 'name:'")

                vname = var['name']
                prompt = utils.template(None, "%s: " % var.get("prompt", vname), self.vars)
                private = var.get("private", True)

                confirm = var.get("confirm", False)
                encrypt = var.get("encrypt", None)
                salt_size = var.get("salt_size", None)
                salt = var.get("salt", None)
                conditional = var.get("only_if", 'True')

                if utils.check_conditional(conditional):
                    vars[vname] = self.playbook.callbacks.on_vars_prompt(vname, private, prompt,encrypt, confirm, salt_size, salt)

        elif type(self.vars_prompt) == dict:
            for (vname, prompt) in self.vars_prompt.iteritems():
                prompt_msg = "%s: " % prompt
                vars[vname] = self.playbook.callbacks.on_vars_prompt(varname=vname, private=False, prompt=prompt_msg)

        else:
            raise errors.AnsibleError("'vars_prompt' section is malformed, see docs")

        results = self.playbook.extra_vars.copy()
        results.update(vars)
        return results

    # *************************************************

    def update_vars_files(self, hosts):
        ''' calculate vars_files, which requires that setup runs first so ansible facts can be mixed in '''

        # now loop through all the hosts...
        for h in hosts:
            self._update_vars_files_for_host(h)

    # *************************************************

    def compare_tags(self, tags):
        ''' given a list of tags that the user has specified, return two lists:
        matched_tags:   tags were found within the current play and match those given
                        by the user
        unmatched_tags: tags that were found within the current play but do not match
                        any provided by the user '''

        # gather all the tags in all the tasks into one list
        all_tags = []
        for task in self._tasks:
            all_tags.extend(task.tags)

        # compare the lists of tags using sets and return the matched and unmatched
        all_tags_set = set(all_tags)
        tags_set = set(tags)
        matched_tags = all_tags_set & tags_set
        unmatched_tags = all_tags_set - tags_set

        return matched_tags, unmatched_tags

    # *************************************************

    def _has_vars_in(self, msg):
        return ((msg.find("$") != -1) or (msg.find("{{") != -1))

    # *************************************************

    def _update_vars_files_for_host(self, host):

        if type(self.vars_files) != list:
            self.vars_files = [ self.vars_files ]

        if (host is not None):
            self.playbook.SETUP_CACHE[host].update(self.vars)

            inventory = self.playbook.inventory
            hostrec = inventory.get_host(host)
            groupz = sorted(inventory.groups_for_host(host), key=lambda g: g.depth)
            groups = [ g.name for g in groupz ]
            basedir = inventory.basedir()
            if basedir is not None:
                for x in groups:
                    path = os.path.join(basedir, "group_vars/%s" % x)
                    if os.path.exists(path):
                        data = utils.parse_yaml_from_file(path)
                        if type(data) != dict:
                            raise errors.AnsibleError("%s must be stored as a dictionary/hash" % path)
                        self.playbook.SETUP_CACHE[host].update(data)
                path = os.path.join(basedir, "host_vars/%s" % hostrec.name)
                if os.path.exists(path):
                    data = utils.parse_yaml_from_file(path)
                    if type(data) != dict:
                        raise errors.AnsibleError("%s must be stored as a dictionary/hash" % path)
                    self.playbook.SETUP_CACHE[host].update(data)

        for filename in self.vars_files:

            if type(filename) == list:

                # loop over all filenames, loading the first one, and failing if # none found
                found = False
                sequence = []
                for real_filename in filename:
                    filename2 = utils.template(self.basedir, real_filename, self.vars)
                    filename3 = filename2
                    if host is not None:
                        filename3 = utils.template(self.basedir, filename2, self.playbook.SETUP_CACHE[host])
                    filename4 = utils.path_dwim(self.basedir, filename3)
                    sequence.append(filename4)
                    if os.path.exists(filename4):
                        found = True
                        data = utils.parse_yaml_from_file(filename4)
                        if type(data) != dict:
                            raise errors.AnsibleError("%s must be stored as a dictionary/hash" % filename4)
                        if host is not None:
                            if self._has_vars_in(filename2) and not self._has_vars_in(filename3):
                                # this filename has variables in it that were fact specific
                                # so it needs to be loaded into the per host SETUP_CACHE
                                self.playbook.SETUP_CACHE[host].update(data)
                                self.playbook.callbacks.on_import_for_host(host, filename4)
                        elif not self._has_vars_in(filename4):
                            # found a non-host specific variable, load into vars and NOT
                            # the setup cache
                            self.vars.update(data)
                    elif host is not None:
                        self.playbook.callbacks.on_not_import_for_host(host, filename4)
                    if found:
                        break
                if not found:
                    raise errors.AnsibleError(
                        "%s: FATAL, no files matched for vars_files import sequence: %s" % (host, sequence)
                    )

            else:
                # just one filename supplied, load it!

                filename2 = utils.template(self.basedir, filename, self.vars)
                filename3 = filename2
                if host is not None:
                    filename3 = utils.template(self.basedir, filename2, self.playbook.SETUP_CACHE[host])
                filename4 = utils.path_dwim(self.basedir, filename3)
                if self._has_vars_in(filename4):
                    return
                new_vars = utils.parse_yaml_from_file(filename4)
                if new_vars:
                    if type(new_vars) != dict:
                        raise errors.AnsibleError("%s must be stored as dictonary/hash: %s" % filename4)
                    if host is not None and self._has_vars_in(filename2) and not self._has_vars_in(filename3):
                        # running a host specific pass and has host specific variables
                        # load into setup cache
                        self.playbook.SETUP_CACHE[host].update(new_vars)
                    elif host is None:
                        # running a non-host specific pass and we can update the global vars instead
                        self.vars.update(new_vars)
