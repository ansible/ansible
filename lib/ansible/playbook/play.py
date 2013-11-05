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
import ansible.constants as C
import pipes
import shlex
import os
import sys

class Play(object):

    __slots__ = [
       'hosts', 'name', 'vars', 'default_vars', 'vars_prompt', 'vars_files',
       'handlers', 'remote_user', 'remote_port', 'included_roles', 'accelerate',
       'accelerate_port', 'accelerate_ipv6', 'sudo', 'sudo_user', 'transport', 'playbook',
       'tags', 'gather_facts', 'serial', '_ds', '_handlers', '_tasks',
       'basedir', 'any_errors_fatal', 'roles', 'max_fail_pct'
    ]

    # to catch typos and so forth -- these are userland names
    # and don't line up 1:1 with how they are stored
    VALID_KEYS = [
       'hosts', 'name', 'vars', 'vars_prompt', 'vars_files',
       'tasks', 'handlers', 'remote_user', 'user', 'port', 'include', 'accelerate', 'accelerate_port', 'accelerate_ipv6',
       'sudo', 'sudo_user', 'connection', 'tags', 'gather_facts', 'serial',
       'any_errors_fatal', 'roles', 'pre_tasks', 'post_tasks', 'max_fail_percentage' 
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

        # We first load the vars files from the datastructure
        # so we have the default variables to pass into the roles
        self.vars_files = ds.get('vars_files', [])
        if not isinstance(self.vars_files, list):
            raise errors.AnsibleError('vars_files must be a list')
        self._update_vars_files_for_host(None)

        # now we load the roles into the datastructure
        self.included_roles = []
        ds = self._load_roles(self.roles, ds)
        
        # and finally re-process the vars files as they may have
        # been updated by the included roles
        self.vars_files = ds.get('vars_files', [])
        if not isinstance(self.vars_files, list):
            raise errors.AnsibleError('vars_files must be a list')
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
        self.remote_user      = ds.get('remote_user', ds.get('user', self.playbook.remote_user))
        self.remote_port      = ds.get('port', self.playbook.remote_port)
        self.sudo             = ds.get('sudo', self.playbook.sudo)
        self.sudo_user        = ds.get('sudo_user', self.playbook.sudo_user)
        self.transport        = ds.get('connection', self.playbook.transport)
        self.gather_facts     = ds.get('gather_facts', None)
        self.remote_port      = self.remote_port
        self.any_errors_fatal = utils.boolean(ds.get('any_errors_fatal', 'false'))
        self.accelerate       = utils.boolean(ds.get('accelerate', 'false'))
        self.accelerate_port  = ds.get('accelerate_port', None)
        self.accelerate_ipv6  = ds.get('accelerate_ipv6', False)
        self.max_fail_pct     = int(ds.get('max_fail_percentage', 100))

        load_vars = {}
        load_vars['playbook_dir'] = self.basedir
        if self.playbook.inventory.basedir() is not None:
            load_vars['inventory_dir'] = self.playbook.inventory.basedir()

        self._tasks      = self._load_tasks(self._ds.get('tasks', []), load_vars)
        self._handlers   = self._load_tasks(self._ds.get('handlers', []), load_vars)


        if self.sudo_user != 'root':
            self.sudo = True


    # *************************************************

    def _get_role_path(self, role):
        """
        Returns the path on disk to the directory containing
        the role directories like tasks, templates, etc. Also 
        returns any variables that were included with the role
        """
        orig_path = template(self.basedir,role,self.vars)

        role_vars = {}
        if type(orig_path) == dict:
            # what, not a path?
            role_name = orig_path.get('role', None)
            if role_name is None:
                raise errors.AnsibleError("expected a role name in dictionary: %s" % orig_path)
            role_vars = orig_path
            orig_path = role_name

        role_path = None

        possible_paths = [
            utils.path_dwim(self.basedir, os.path.join('roles', orig_path)),
            utils.path_dwim(self.basedir, orig_path)
        ]

        if C.DEFAULT_ROLES_PATH:
            search_locations = C.DEFAULT_ROLES_PATH.split(os.pathsep)
            for loc in search_locations:
                possible_paths.append(utils.path_dwim(loc, orig_path))

        for path_option in possible_paths:
            if os.path.isdir(path_option):
                role_path = path_option
                break

        if role_path is None:
            raise errors.AnsibleError("cannot find role in %s" % " or ".join(possible_paths))

        return (role_path, role_vars)

    def _build_role_dependencies(self, roles, dep_stack, passed_vars={}, level=0):
        # this number is arbitrary, but it seems sane
        if level > 20:
            raise errors.AnsibleError("too many levels of recursion while resolving role dependencies")
        for role in roles:
            role_path,role_vars = self._get_role_path(role)
            role_vars = utils.combine_vars(passed_vars, role_vars)
            vars = self._resolve_main(utils.path_dwim(self.basedir, os.path.join(role_path, 'vars')))
            vars_data = {}
            if os.path.isfile(vars):
                vars_data = utils.parse_yaml_from_file(vars)
                if vars_data:
                    role_vars = utils.combine_vars(vars_data, role_vars)
            defaults = self._resolve_main(utils.path_dwim(self.basedir, os.path.join(role_path, 'defaults')))
            defaults_data = {}
            if os.path.isfile(defaults):
                defaults_data = utils.parse_yaml_from_file(defaults)
            # the meta directory contains the yaml that should
            # hold the list of dependencies (if any)
            meta = self._resolve_main(utils.path_dwim(self.basedir, os.path.join(role_path, 'meta')))
            if os.path.isfile(meta):
                data = utils.parse_yaml_from_file(meta)
                if data:
                    dependencies = data.get('dependencies',[])
                    for dep in dependencies:
                        allow_dupes = False
                        (dep_path,dep_vars) = self._get_role_path(dep)
                        meta = self._resolve_main(utils.path_dwim(self.basedir, os.path.join(dep_path, 'meta')))
                        if os.path.isfile(meta):
                            meta_data = utils.parse_yaml_from_file(meta)
                            if meta_data:
                                allow_dupes = utils.boolean(meta_data.get('allow_duplicates',''))

                        # if tags are set from this role, merge them
                        # into the tags list for the dependent role
                        if "tags" in passed_vars:
                            for included_role_dep in dep_stack:
                                included_dep_name = included_role_dep[0]
                                included_dep_vars = included_role_dep[2]
                                if included_dep_name == dep:
                                    if "tags" in included_dep_vars:
                                        included_dep_vars["tags"] = list(set(included_dep_vars["tags"] + passed_vars["tags"]))
                                    else:
                                        included_dep_vars["tags"] = passed_vars["tags"].copy()

                        dep_vars = utils.combine_vars(passed_vars, dep_vars)
                        dep_vars = utils.combine_vars(role_vars, dep_vars)
                        vars = self._resolve_main(utils.path_dwim(self.basedir, os.path.join(dep_path, 'vars')))
                        vars_data = {}
                        if os.path.isfile(vars):
                            vars_data = utils.parse_yaml_from_file(vars)
                            if vars_data:
                                dep_vars = utils.combine_vars(vars_data, dep_vars)
                        defaults = self._resolve_main(utils.path_dwim(self.basedir, os.path.join(dep_path, 'defaults')))
                        dep_defaults_data = {}
                        if os.path.isfile(defaults):
                            dep_defaults_data = utils.parse_yaml_from_file(defaults)
                        if 'role' in dep_vars:
                            del dep_vars['role']

                        if "tags" in passed_vars:
                            if not self._is_valid_tag(passed_vars["tags"]):
                                # one of the tags specified for this role was in the
                                # skip list, or we're limiting the tags and it didn't 
                                # match one, so we just skip it completely
                                continue

                        if not allow_dupes:
                            if dep in self.included_roles:
                                # skip back to the top, since we don't want to
                                # do anything else with this role
                                continue
                            else:
                                self.included_roles.append(dep)

                        # pass along conditionals from roles to dep roles
                        if type(role) is dict:
                            if 'when' in passed_vars:
                                if 'when' in dep_vars:
                                    tmpcond = []

                                    if type(passed_vars['when']) is str:
                                        tmpcond.append(passed_vars['when'])
                                    elif type(passed_vars['when']) is list:
                                        tmpcond.join(passed_vars['when'])

                                    if type(dep_vars['when']) is str:
                                        tmpcond.append(dep_vars['when'])
                                    elif type(dep_vars['when']) is list:
                                        tmpcond += dep_vars['when']

                                    if len(tmpcond) > 0:
                                        dep_vars['when'] = tmpcond
                                else:
                                    dep_vars['when'] = passed_vars['when']

                        self._build_role_dependencies([dep], dep_stack, passed_vars=dep_vars, level=level+1)
                        dep_stack.append([dep,dep_path,dep_vars,dep_defaults_data])

            # only add the current role when we're at the top level,
            # otherwise we'll end up in a recursive loop 
            if level == 0:
                self.included_roles.append(role)
                dep_stack.append([role,role_path,role_vars,defaults_data])
        return dep_stack

    def _load_role_defaults(self, defaults_files):
        # process default variables
        default_vars = {}
        for filename in defaults_files:
            if os.path.exists(filename):
                new_default_vars = utils.parse_yaml_from_file(filename)
                if new_default_vars:
                    if type(new_default_vars) != dict:
                        raise errors.AnsibleError("%s must be stored as dictionary/hash: %s" % (filename, type(new_default_vars)))

                    default_vars = utils.combine_vars(default_vars, new_default_vars)

        return default_vars

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
        defaults_files = []

        pre_tasks = ds.get('pre_tasks', None)
        if type(pre_tasks) != list:
            pre_tasks = []
        for x in pre_tasks:
            new_tasks.append(x)

        # flush handlers after pre_tasks
        new_tasks.append(dict(meta='flush_handlers'))

        roles = self._build_role_dependencies(roles, [], self.vars)

        for (role,role_path,role_vars,default_vars) in roles:
            # special vars must be extracted from the dict to the included tasks
            special_keys = [ "sudo", "sudo_user", "when", "with_items" ]
            special_vars = {}
            for k in special_keys:
                if k in role_vars:
                    special_vars[k] = role_vars[k]

            task_basepath     = utils.path_dwim(self.basedir, os.path.join(role_path, 'tasks'))
            handler_basepath  = utils.path_dwim(self.basedir, os.path.join(role_path, 'handlers'))
            vars_basepath     = utils.path_dwim(self.basedir, os.path.join(role_path, 'vars'))
            meta_basepath     = utils.path_dwim(self.basedir, os.path.join(role_path, 'meta'))
            defaults_basepath = utils.path_dwim(self.basedir, os.path.join(role_path, 'defaults'))

            task      = self._resolve_main(task_basepath)
            handler   = self._resolve_main(handler_basepath)
            vars_file = self._resolve_main(vars_basepath)
            meta_file = self._resolve_main(meta_basepath)
            defaults_file = self._resolve_main(defaults_basepath)

            library   = utils.path_dwim(self.basedir, os.path.join(role_path, 'library'))

            missing = lambda f: not os.path.isfile(f)
            if missing(task) and missing(handler) and missing(vars_file) and missing(defaults_file) and missing(meta_file) and missing(library):
                raise errors.AnsibleError("found role at %s, but cannot find %s or %s or %s or %s or %s or %s" % (role_path, task, handler, vars_file, defaults_file, meta_file, library))

            if isinstance(role, dict):
                role_name = role['role']
            else:
                role_name = role

            if os.path.isfile(task):
                nt = dict(include=pipes.quote(task), vars=role_vars, default_vars=default_vars, role_name=role_name)
                for k in special_keys:
                    if k in special_vars:
                        nt[k] = special_vars[k]
                new_tasks.append(nt)
            if os.path.isfile(handler):
                nt = dict(include=pipes.quote(handler), vars=role_vars, role_name=role_name)
                for k in special_keys:
                    if k in special_vars:
                        nt[k] = special_vars[k]
                new_handlers.append(nt)
            if os.path.isfile(vars_file):
                new_vars_files.append(vars_file)
            if os.path.isfile(defaults_file):
                defaults_files.append(defaults_file)
            if os.path.isdir(library):
                utils.plugins.module_finder.add_directory(library)

        tasks      = ds.get('tasks', None)
        post_tasks = ds.get('post_tasks', None)
        handlers   = ds.get('handlers', None)
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

        self.default_vars = self._load_role_defaults(defaults_files)

        return ds

    # *************************************************

    def _resolve_main(self, basepath):
        ''' flexibly handle variations in main filenames '''
        # these filenames are acceptable:
        mains = (
                 os.path.join(basepath, 'main'),
                 os.path.join(basepath, 'main.yml'),
                 os.path.join(basepath, 'main.yaml'),
                )
        if sum([os.path.isfile(x) for x in mains]) > 1:
            raise errors.AnsibleError("found multiple main files at %s, only one allowed" % (basepath))
        else:
            for m in mains:
                if os.path.isfile(m):
                    return m # exactly one main file
            return mains[0] # zero mains (we still need to return something)

    # *************************************************

    def _load_tasks(self, tasks, vars=None, default_vars=None, sudo_vars=None, additional_conditions=None, original_file=None, role_name=None):
        ''' handle task and handler include statements '''

        results = []
        if tasks is None:
            # support empty handler files, and the like.
            tasks = []
        if additional_conditions is None:
            additional_conditions = []
        if vars is None:
            vars = {}
        if default_vars is None:
            default_vars = {}
        if sudo_vars is None:
            sudo_vars = {}

        old_conditions = list(additional_conditions)

        for x in tasks:

            # prevent assigning the same conditions to each task on an include
            included_additional_conditions = list(old_conditions)

            if not isinstance(x, dict):
                raise errors.AnsibleError("expecting dict; got: %s" % x)

            # evaluate sudo vars for current and child tasks 
            included_sudo_vars = {}
            for k in ["sudo", "sudo_user"]:
                if k in x:
                    included_sudo_vars[k] = x[k]
                elif k in sudo_vars:
                    included_sudo_vars[k] = sudo_vars[k]
                    x[k] = sudo_vars[k]

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
                include_vars = {}
                for k in x:
                    if k.startswith("with_"):
                        utils.deprecated("include + with_items is an unsupported feature and has been undocumented for many releases because of this", "1.5")
                        plugin_name = k[5:]
                        if plugin_name not in utils.plugins.lookup_loader:
                            raise errors.AnsibleError("cannot find lookup plugin named %s for usage in with_%s" % (plugin_name, plugin_name))
                        terms = template(self.basedir, x[k], task_vars)
                        items = utils.plugins.lookup_loader.get(plugin_name, basedir=self.basedir, runner=None).run(terms, inject=task_vars)
                    elif k.startswith("when_"):
                        included_additional_conditions.insert(0, utils.compile_when_to_only_if("%s %s" % (k[5:], x[k])))
                    elif k == 'when':
                        if type(x[k]) is str:
                            included_additional_conditions.insert(0, utils.compile_when_to_only_if("jinja2_compare %s" % x[k]))
                        elif type(x[k]) is list:
                            for i in x[k]:
                                included_additional_conditions.insert(0, utils.compile_when_to_only_if("jinja2_compare %s" % i))
                    elif k in ("include", "vars", "default_vars", "only_if", "sudo", "sudo_user", "role_name"):
                        continue
                    else:
                        include_vars[k] = x[k]

                default_vars = x.get('default_vars', {})
                if not default_vars:
                    default_vars = self.default_vars
                else:
                    default_vars = utils.combine_vars(self.default_vars, default_vars)

                # append the vars defined with the include (from above) 
                # as well as the old-style 'vars' element. The old-style
                # vars are given higher precedence here (just in case)
                task_vars = utils.combine_vars(task_vars, include_vars)
                if 'vars' in x:
                    task_vars = utils.combine_vars(task_vars, x['vars'])

                if 'only_if' in x:
                    included_additional_conditions.append(x['only_if'])

                new_role = None
                if 'role_name' in x:
                    new_role = x['role_name']

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
                    if 'role_name' in x and data is not None:
                        for x in data:
                            if 'include' in x:
                                x['role_name'] = new_role
                    loaded = self._load_tasks(data, mv, default_vars, included_sudo_vars, list(included_additional_conditions), original_file=include_filename, role_name=new_role)
                    results += loaded
            elif type(x) == dict:
                task = Task(self,x,module_vars=task_vars,default_vars=default_vars,additional_conditions=list(additional_conditions),role_name=role_name)
                results.append(task)
            else:
                raise Exception("unexpected task type")

        for x in results:
            if self.tags is not None:
                x.tags.extend(self.tags)

        return results

    # *************************************************

    def _is_valid_tag(self, tag_list):
        """
        Check to see if the list of tags passed in is in the list of tags 
        we only want (playbook.only_tags), or if it is not in the list of 
        tags we don't want (playbook.skip_tags).
        """
        matched_skip_tags = set(tag_list) & set(self.playbook.skip_tags)
        matched_only_tags = set(tag_list) & set(self.playbook.only_tags)
        if len(matched_skip_tags) > 0 or (self.playbook.only_tags != ['all'] and len(matched_only_tags) == 0):
            return False
        return True

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
                        raise errors.AnsibleError("%s must be stored as dictionary/hash: %s" % (filename4, type(new_vars)))
                    if host is not None and self._has_vars_in(filename2) and not self._has_vars_in(filename3):
                        # running a host specific pass and has host specific variables
                        # load into setup cache
                        self.playbook.SETUP_CACHE[host] = utils.combine_vars(
                            self.playbook.SETUP_CACHE[host], new_vars)
                        self.playbook.callbacks.on_import_for_host(host, filename4)
                    elif host is None:
                        # running a non-host specific pass and we can update the global vars instead
                        self.vars = utils.combine_vars(self.vars, new_vars)
