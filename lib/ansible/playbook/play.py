# (c) 2012-2013, Michael DeHaan <michael.dehaan@gmail.com>
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

from ansible.utils.template import template
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
       'basedir', 'any_errors_fatal', 'roles'
    ]

    # to catch typos and so forth -- these are userland names
    # and don't line up 1:1 with how they are stored
    VALID_KEYS = [
       'hosts', 'name', 'vars', 'vars_prompt', 'vars_files',
       'tasks', 'handlers', 'user', 'port', 'include',
       'sudo', 'sudo_user', 'connection', 'tags', 'gather_facts', 'serial',
       'any_errors_fatal', 'roles', 'pre_tasks', 'post_tasks'
    ]

    # *************************************************

    def __init__(self, playbook, ds, basedir):
        ''' constructor loads from a play datastructure '''

        for x in ds.keys():
            if not x in Play.VALID_KEYS:
                raise errors.AnsibleError("%s is not a legal parameter in an Ansible Playbook" % x)

        # allow all playbook keys to be set by --extra-vars
        self.vars             = ds.get('vars', {})
        self.vars_prompt      = ds.get('vars_prompt', {})
        self.playbook         = playbook
        self.vars             = self._get_vars()
        self.basedir          = basedir
        self.roles            = ds.get('roles', None)
        self.tags             = ds.get('tags', None)

        if self.tags is None:
            self.tags = []
        elif type(self.tags) in [ str, unicode ]:
            self.tags = self.tags.split(",")
        elif type(self.tags) != list:
            self.tags = []

        ds = self._load_roles(self.roles, ds)
        self.vars_files       = ds.get('vars_files', [])

        self._update_vars_files_for_host(None)

        # template everything to be efficient, but do not pre-mature template
        # tasks/handlers as they may have inventory scope overrides
        _tasks    = ds.pop('tasks', [])
        _handlers = ds.pop('handlers', [])
        ds = template(basedir, ds, self.vars) 
        ds['tasks'] = _tasks
        ds['handlers'] = _handlers

        self._ds = ds         

        hosts = ds.get('hosts')
        if hosts is None:
            raise errors.AnsibleError('hosts declaration is required')
        elif isinstance(hosts, list):
            hosts = ';'.join(hosts)

        self.serial           = int(ds.get('serial', 0))
        self.hosts            = hosts
        self.name             = ds.get('name', self.hosts)
        self._tasks           = ds.get('tasks', [])
        self._handlers        = ds.get('handlers', [])
        self.remote_user      = ds.get('user', self.playbook.remote_user)
        self.remote_port      = ds.get('port', self.playbook.remote_port)
        self.sudo             = ds.get('sudo', self.playbook.sudo)
        self.sudo_user        = ds.get('sudo_user', self.playbook.sudo_user)
        self.transport        = ds.get('connection', self.playbook.transport)
        self.gather_facts     = ds.get('gather_facts', None)
        self.serial           = int(ds.get('serial', 0))
        self.remote_port      = self.remote_port
        self.any_errors_fatal = ds.get('any_errors_fatal', False)

        load_vars = {}
        if self.playbook.inventory.basedir() is not None:
            load_vars['inventory_dir'] = self.playbook.inventory.basedir()

        self._tasks      = self._load_tasks(self._ds.get('tasks', []), load_vars)
        self._handlers   = self._load_tasks(self._ds.get('handlers', []), load_vars)


        if self.sudo_user != 'root':
            self.sudo = True
        

    # *************************************************

    def _load_roles(self, roles, ds):


        # a role is a name that auto-includes the following if they exist
        #    <rolename>/tasks/main.yml
        #    <rolename>/handlers/main.yml
        #    <rolename>/vars/main.yml
        #    <rolename>/library
        # and it auto-extends tasks/handlers/vars_files/module paths as appropriate if found

        if roles is None:
            roles = []
        if type(roles) != list:
            raise errors.AnsibleError("value of 'roles:' must be a list")

        new_tasks = []
        new_handlers = []
        new_vars_files = []

        pre_tasks = ds.get('pre_tasks', None)
        if type(pre_tasks) != list:
            pre_tasks = []
        for x in pre_tasks:
            new_tasks.append(x)

        # flush handlers after pre_tasks
        new_tasks.append(dict(meta='flush_handlers'))

        # variables if the role was parameterized (i.e. given as a hash) 
        has_dict = {}

        for orig_path in roles:

            if type(orig_path) == dict:
                # what, not a path?
                role_name = orig_path.get('role', None)
                if role_name is None:
                    raise errors.AnsibleError("expected a role name in dictionary: %s" % orig_path)
                has_dict = orig_path
                orig_path = role_name

            with_items = has_dict.get('with_items', None)
            when       = has_dict.get('when', None)

            path = utils.path_dwim(self.basedir, os.path.join('roles', orig_path))
            if not os.path.isdir(path) and not orig_path.startswith(".") and not orig_path.startswith("/"):
                path2 = utils.path_dwim(self.basedir, orig_path)
                if not os.path.isdir(path2):
                    raise errors.AnsibleError("cannot find role in %s or %s" % (path, path2))
                path = path2
            elif not os.path.isdir(path):
                raise errors.AnsibleError("cannot find role in %s" % (path))
            task      = utils.path_dwim(self.basedir, os.path.join(path, 'tasks', 'main.yml'))
            handler   = utils.path_dwim(self.basedir, os.path.join(path, 'handlers', 'main.yml'))
            vars_file = utils.path_dwim(self.basedir, os.path.join(path, 'vars', 'main.yml'))
            library   = utils.path_dwim(self.basedir, os.path.join(path, 'library'))
            if not os.path.isfile(task) and not os.path.isfile(handler) and not os.path.isfile(vars_file) and not os.path.isdir(library):
                raise errors.AnsibleError("found role at %s, but cannot find %s or %s or %s or %s" % (path, task, handler, vars_file, library))
            if os.path.isfile(task):
                nt = dict(include=task, vars=has_dict)
                if when: 
                    nt['when'] = when
                if with_items:
                    nt['with_items'] = with_items
                new_tasks.append(nt)
            if os.path.isfile(handler):
                nt = dict(include=handler, vars=has_dict)
                if when: 
                    nt['when'] = when
                if with_items:
                    nt['with_items'] = with_items
                new_handlers.append(nt)
            if os.path.isfile(vars_file):
                new_vars_files.append(vars_file)
            if os.path.isdir(library):
                utils.plugins.module_finder.add_directory(library)

        tasks = ds.get('tasks', None)
        post_tasks = ds.get('post_tasks', None)

        handlers = ds.get('handlers', None)
        vars_files = ds.get('vars_files', None)

        if type(tasks) != list:
            tasks = []
        if type(handlers) != list:
            handlers = []
        if type(vars_files) != list:
            vars_files = []
        if type(post_tasks) != list:
            post_tasks = []

        new_tasks.extend(tasks)
        # flush handlers after tasks + role tasks
        new_tasks.append(dict(meta='flush_handlers'))
        new_tasks.extend(post_tasks)
        # flush handlers after post tasks
        new_tasks.append(dict(meta='flush_handlers'))
        new_handlers.extend(handlers)
        new_vars_files.extend(vars_files)
        ds['tasks'] = new_tasks
        ds['handlers'] = new_handlers
        ds['vars_files'] = new_vars_files

        return ds

    # *************************************************

    def _load_tasks(self, tasks, vars={}, additional_conditions=[], original_file=None):
        ''' handle task and handler include statements '''

        results = []
        if tasks is None:
            # support empty handler files, and the like.
            tasks = []

        for x in tasks:
            if not isinstance(x, dict):
                raise errors.AnsibleError("expecting dict; got: %s" % x)

            if 'meta' in x:
                if x['meta'] == 'flush_handlers':
                    results.append(Task(self,x))
                    continue
 
            task_vars = self.vars.copy()
            task_vars.update(vars)
            if original_file:
                task_vars['_original_file'] = original_file

            if 'include' in x:
                tokens = shlex.split(str(x['include']))
                items = ['']
                included_additional_conditions = list(additional_conditions)
                for k in x:
                    if k.startswith("with_"):
                        plugin_name = k[5:]
                        if plugin_name not in utils.plugins.lookup_loader:
                            raise errors.AnsibleError("cannot find lookup plugin named %s for usage in with_%s" % (plugin_name, plugin_name))
                        terms = template(self.basedir, x[k], task_vars)
                        items = utils.plugins.lookup_loader.get(plugin_name, basedir=self.basedir, runner=None).run(terms, inject=task_vars)
                    elif k.startswith("when_"):
                        included_additional_conditions.append(utils.compile_when_to_only_if("%s %s" % (k[5:], x[k])))
                    elif k == 'when':
                        included_additional_conditions.append(utils.compile_when_to_only_if("jinja2_compare %s" % x[k]))
                    elif k in ("include", "vars", "only_if"):
                        pass
                    else:
                        raise errors.AnsibleError("parse error: task includes cannot be used with other directives: %s" % k)

                if 'vars' in x:
                    task_vars.update(x['vars'])
                if 'only_if' in x:
                    included_additional_conditions.append(x['only_if'])

                for item in items:
                    mv = task_vars.copy()
                    mv['item'] = item
                    for t in tokens[1:]:
                        (k,v) = t.split("=", 1)
                        mv[k] = template(self.basedir, v, mv)
                    dirname = self.basedir
                    if original_file:
                        dirname = os.path.dirname(original_file)     
                    include_file = template(dirname, tokens[0], mv)
                    include_filename = utils.path_dwim(dirname, include_file)
                    data = utils.parse_yaml_from_file(include_filename)
                    results += self._load_tasks(data, mv, included_additional_conditions, original_file=include_filename)
            elif type(x) == dict:
                results.append(Task(self,x,module_vars=task_vars, additional_conditions=additional_conditions))
            else:
                raise Exception("unexpected task type")

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

        vars = {}

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
                prompt = var.get("prompt", vname)
                default = var.get("default", None)
                private = var.get("private", True)

                confirm = var.get("confirm", False)
                encrypt = var.get("encrypt", None)
                salt_size = var.get("salt_size", None)
                salt = var.get("salt", None)

                if vname not in self.playbook.extra_vars:
                    vars[vname] = self.playbook.callbacks.on_vars_prompt(
                                     vname, private, prompt, encrypt, confirm, salt_size, salt, default
                                  )

        elif type(self.vars_prompt) == dict:
            for (vname, prompt) in self.vars_prompt.iteritems():
                prompt_msg = "%s: " % prompt
                if vname not in self.playbook.extra_vars:
                    vars[vname] = self.playbook.callbacks.on_vars_prompt(
                                     varname=vname, private=False, prompt=prompt_msg, default=None
                                  )

        else:
            raise errors.AnsibleError("'vars_prompt' section is malformed, see docs")

        if type(self.playbook.extra_vars) == dict:
            vars.update(self.playbook.extra_vars)

        return vars

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
            if not task.meta:
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

        if host is not None:
            inject = {}
            inject.update(self.playbook.inventory.get_variables(host))
            inject.update(self.playbook.SETUP_CACHE[host])

        for filename in self.vars_files:

            if type(filename) == list:

                # loop over all filenames, loading the first one, and failing if # none found
                found = False
                sequence = []
                for real_filename in filename:
                    filename2 = template(self.basedir, real_filename, self.vars)
                    filename3 = filename2
                    if host is not None:
                        filename3 = template(self.basedir, filename2, inject)
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
                if not found and host is not None:
                    raise errors.AnsibleError(
                        "%s: FATAL, no files matched for vars_files import sequence: %s" % (host, sequence)
                    )

            else:
                # just one filename supplied, load it!

                filename2 = template(self.basedir, filename, self.vars)
                filename3 = filename2
                if host is not None:
                    filename3 = template(self.basedir, filename2, inject)
                filename4 = utils.path_dwim(self.basedir, filename3)
                if self._has_vars_in(filename4):
                    continue
                new_vars = utils.parse_yaml_from_file(filename4)
                if new_vars:
                    if type(new_vars) != dict:
                        raise errors.AnsibleError("%s must be stored as dictonary/hash: %s" % (filename4, type(new_vars)))
                    if host is not None and self._has_vars_in(filename2) and not self._has_vars_in(filename3):
                        # running a host specific pass and has host specific variables
                        # load into setup cache
                        self.playbook.SETUP_CACHE[host] = utils.combine_vars(
                            self.playbook.SETUP_CACHE[host], new_vars)
                        self.playbook.callbacks.on_import_for_host(host, filename4)
                    elif host is None:
                        # running a non-host specific pass and we can update the global vars instead
                        self.vars = utils.combine_vars(self.vars, new_vars)
