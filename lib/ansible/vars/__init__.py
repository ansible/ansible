# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from collections import defaultdict
from collections import MutableMapping

from ansible.compat.six import iteritems
from jinja2.exceptions import UndefinedError

try:
    from hashlib import sha1
except ImportError:
    from sha import sha as sha1

from ansible import constants as C
from ansible.cli import CLI
from ansible.compat.six import string_types, text_type
from ansible.errors import AnsibleError, AnsibleParserError, AnsibleUndefinedVariable, AnsibleFileNotFound
from ansible.inventory.host import Host
from ansible.plugins import lookup_loader
from ansible.plugins.cache import FactCache
from ansible.template import Templar
from ansible.utils.debug import debug
from ansible.utils.listify import listify_lookup_plugin_terms
from ansible.utils.vars import combine_vars
from ansible.vars.unsafe_proxy import wrap_var

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

VARIABLE_CACHE = dict()
HOSTVARS_CACHE = dict()

def preprocess_vars(a):
    '''
    Ensures that vars contained in the parameter passed in are
    returned as a list of dictionaries, to ensure for instance
    that vars loaded from a file conform to an expected state.
    '''

    if a is None:
        return None
    elif not isinstance(a, list):
        data = [ a ]
    else:
        data = a

    for item in data:
        if not isinstance(item, MutableMapping):
            raise AnsibleError("variable files must contain either a dictionary of variables, or a list of dictionaries. Got: %s (%s)" % (a, type(a)))

    return data

def strip_internal_keys(dirty):
    '''
    All keys stating with _ansible_ are internal, so create a copy of the 'dirty' dict
    and remove them from the clean one before returning it
    '''
    clean = dirty.copy()
    for k in dirty.keys():
        if isinstance(k, string_types) and k.startswith('_ansible_'):
            del clean[k]
    return clean

class VariableManager:

    def __init__(self):

        self._fact_cache = FactCache()
        self._nonpersistent_fact_cache = defaultdict(dict)
        self._vars_cache = defaultdict(dict)
        self._extra_vars = defaultdict(dict)
        self._host_vars_files = defaultdict(dict)
        self._group_vars_files = defaultdict(dict)
        self._inventory = None
        self._omit_token = '__omit_place_holder__%s' % sha1(os.urandom(64)).hexdigest()

    def __getstate__(self):
        data = dict(
            fact_cache = self._fact_cache,
            np_fact_cache = self._nonpersistent_fact_cache,
            vars_cache = self._vars_cache,
            extra_vars = self._extra_vars,
            host_vars_files = self._host_vars_files,
            group_vars_files = self._group_vars_files,
            omit_token = self._omit_token,
            #inventory = self._inventory,
        )
        return data

    def __setstate__(self, data):
        self._fact_cache = data.get('fact_cache', defaultdict(dict))
        self._nonpersistent_fact_cache = data.get('np_fact_cache', defaultdict(dict))
        self._vars_cache = data.get('vars_cache', defaultdict(dict))
        self._extra_vars = data.get('extra_vars', dict())
        self._host_vars_files = data.get('host_vars_files', defaultdict(dict))
        self._group_vars_files = data.get('group_vars_files', defaultdict(dict))
        self._omit_token = data.get('omit_token', '__omit_place_holder__%s' % sha1(os.urandom(64)).hexdigest())
        self._inventory = data.get('inventory', None)

    def _get_cache_entry(self, play=None, host=None, task=None):
        play_id = "NONE"
        if play:
            play_id = play._uuid

        host_id = "NONE"
        if host:
            host_id = host.get_name()

        task_id = "NONE"
        if task:
            task_id = task._uuid

        return "PLAY:%s;HOST:%s;TASK:%s" % (play_id, host_id, task_id)

    @property
    def extra_vars(self):
        ''' ensures a clean copy of the extra_vars are made '''
        return self._extra_vars.copy()

    @extra_vars.setter
    def extra_vars(self, value):
        ''' ensures a clean copy of the extra_vars are used to set the value '''
        assert isinstance(value, MutableMapping)
        self._extra_vars = value.copy()

    def set_inventory(self, inventory):
        self._inventory = inventory

    def _preprocess_vars(self, a):
        '''
        Ensures that vars contained in the parameter passed in are
        returned as a list of dictionaries, to ensure for instance
        that vars loaded from a file conform to an expected state.
        '''

        if a is None:
            return None
        elif not isinstance(a, list):
            data = [ a ]
        else:
            data = a

        for item in data:
            if not isinstance(item, MutableMapping):
                raise AnsibleError("variable files must contain either a dictionary of variables, or a list of dictionaries. Got: %s (%s)" % (a, type(a)))

        return data

    # FIXME: include_hostvars is no longer used, and should be removed, but
    #        all other areas of code calling get_vars need to be fixed too
    def get_vars(self, loader, play=None, host=None, task=None, include_hostvars=True, include_delegate_to=True, use_cache=True):
        '''
        Returns the variables, with optional "context" given via the parameters
        for the play, host, and task (which could possibly result in different
        sets of variables being returned due to the additional context).

        The order of precedence is:
        - play->roles->get_default_vars (if there is a play context)
        - group_vars_files[host] (if there is a host context)
        - host_vars_files[host] (if there is a host context)
        - host->get_vars (if there is a host context)
        - fact_cache[host] (if there is a host context)
        - play vars (if there is a play context)
        - play vars_files (if there's no host context, ignore
          file names that cannot be templated)
        - task->get_vars (if there is a task context)
        - vars_cache[host] (if there is a host context)
        - extra vars
        '''

        debug("in VariableManager get_vars()")
        cache_entry = self._get_cache_entry(play=play, host=host, task=task)
        if cache_entry in VARIABLE_CACHE and use_cache:
            debug("vars are cached, returning them now")
            return VARIABLE_CACHE[cache_entry]

        all_vars = dict()
        magic_variables = self._get_magic_variables(
            loader=loader,
            play=play,
            host=host,
            task=task,
            include_hostvars=include_hostvars,
            include_delegate_to=include_delegate_to,
        )

        if play:
            # first we compile any vars specified in defaults/main.yml
            # for all roles within the specified play
            for role in play.get_roles():
                all_vars = combine_vars(all_vars, role.get_default_vars())

            # if we have a task in this context, and that task has a role, make
            # sure it sees its defaults above any other roles, as we previously
            # (v1) made sure each task had a copy of its roles default vars
            if task and task._role is not None:
                all_vars = combine_vars(all_vars, task._role.get_default_vars())

        if host:
            # next, if a host is specified, we load any vars from group_vars
            # files and then any vars from host_vars files which may apply to
            # this host or the groups it belongs to

            # we merge in vars from groups specified in the inventory (INI or script)
            all_vars = combine_vars(all_vars, host.get_group_vars())

            # then we merge in the special 'all' group_vars first, if they exist
            if 'all' in self._group_vars_files:
                data = preprocess_vars(self._group_vars_files['all'])
                for item in data:
                    all_vars = combine_vars(all_vars, item)

            for group in sorted(host.get_groups(), key=lambda g: g.depth):
                if group.name in self._group_vars_files and group.name != 'all':
                    for data in self._group_vars_files[group.name]:
                        data = preprocess_vars(data)
                        for item in data:
                            all_vars = combine_vars(all_vars, item)

            # then we merge in vars from the host specified in the inventory (INI or script)
            all_vars = combine_vars(all_vars, host.get_vars())

            # then we merge in the host_vars/<hostname> file, if it exists
            host_name = host.get_name()
            if host_name in self._host_vars_files:
                for data in self._host_vars_files[host_name]:
                    data = preprocess_vars(data)
                    for item in data:
                        all_vars = combine_vars(all_vars, item)

            # finally, the facts caches for this host, if it exists
            try:
                host_facts = wrap_var(self._fact_cache.get(host.name, dict()))
                all_vars = combine_vars(all_vars, host_facts)
            except KeyError:
                pass

        if play:
            all_vars = combine_vars(all_vars, play.get_vars())

            for vars_file_item in play.get_vars_files():
                # create a set of temporary vars here, which incorporate the extra
                # and magic vars so we can properly template the vars_files entries
                temp_vars = combine_vars(all_vars, self._extra_vars)
                temp_vars = combine_vars(temp_vars, magic_variables)
                templar = Templar(loader=loader, variables=temp_vars)

                # we assume each item in the list is itself a list, as we
                # support "conditional includes" for vars_files, which mimics
                # the with_first_found mechanism.
                vars_file_list = vars_file_item
                if not isinstance(vars_file_list, list):
                     vars_file_list = [ vars_file_list ]

                # now we iterate through the (potential) files, and break out
                # as soon as we read one from the list. If none are found, we
                # raise an error, which is silently ignored at this point.
                try:
                    for vars_file in vars_file_list:
                        vars_file = templar.template(vars_file)
                        try:
                            data = preprocess_vars(loader.load_from_file(vars_file))
                            if data is not None:
                                for item in data:
                                    all_vars = combine_vars(all_vars, item)
                            break
                        except AnsibleFileNotFound as e:
                            # we continue on loader failures
                            continue
                        except AnsibleParserError as e:
                            raise
                    else:
                        raise AnsibleFileNotFound("vars file %s was not found" % vars_file_item)
                except (UndefinedError, AnsibleUndefinedVariable):
                    if host is not None and self._fact_cache.get(host.name, dict()).get('module_setup') and task is not None:
                        raise AnsibleUndefinedVariable("an undefined variable was found when attempting to template the vars_files item '%s'" % vars_file_item, obj=vars_file_item)
                    else:
                        # we do not have a full context here, and the missing variable could be
                        # because of that, so just show a warning and continue
                        display.vvv("skipping vars_file '%s' due to an undefined variable" % vars_file_item)
                        continue

            if not C.DEFAULT_PRIVATE_ROLE_VARS:
                for role in play.get_roles():
                    all_vars = combine_vars(all_vars, role.get_role_params())
                    all_vars = combine_vars(all_vars, role.get_vars(include_params=False))

        if task:
            if task._role:
                all_vars = combine_vars(all_vars, task._role.get_vars())
            all_vars = combine_vars(all_vars, task.get_vars())

        if host:
            all_vars = combine_vars(all_vars, self._vars_cache.get(host.get_name(), dict()))
            all_vars = combine_vars(all_vars, self._nonpersistent_fact_cache.get(host.name, dict()))

        # special case for include tasks, where the include params
        # may be specified in the vars field for the task, which should
        # have higher precedence than the vars/np facts above
        if task:
            all_vars = combine_vars(all_vars, task.get_include_params())

        all_vars = combine_vars(all_vars, self._extra_vars)
        all_vars = combine_vars(all_vars, magic_variables)

        # special case for the 'environment' magic variable, as someone
        # may have set it as a variable and we don't want to stomp on it
        if task:
            if  'environment' not in all_vars:
                all_vars['environment'] = task.environment
            else:
                display.warning("The variable 'environment' appears to be used already, which is also used internally for environment variables set on the task/block/play. You should use a different variable name to avoid conflicts with this internal variable")

        # if we have a task and we're delegating to another host, figure out the
        # variables for that host now so we don't have to rely on hostvars later
        if task and task.delegate_to is not None and include_delegate_to:
            all_vars['ansible_delegated_vars'] = self._get_delegated_vars(loader, play, task, all_vars)

        #VARIABLE_CACHE[cache_entry] = all_vars
        if task or play:
            all_vars['vars'] = all_vars.copy()

        debug("done with get_vars()")
        return all_vars

    def invalidate_hostvars_cache(self, play):
        hostvars_cache_entry = self._get_cache_entry(play=play)
        if hostvars_cache_entry in HOSTVARS_CACHE:
            del HOSTVARS_CACHE[hostvars_cache_entry]

    def _get_magic_variables(self, loader, play, host, task, include_hostvars, include_delegate_to):
        '''
        Returns a dictionary of so-called "magic" variables in Ansible,
        which are special variables we set internally for use.
        '''

        variables = dict()
        variables['playbook_dir'] = loader.get_basedir()

        if host:
            variables['group_names'] = sorted([group.name for group in host.get_groups() if group.name != 'all'])

            if self._inventory is not None:
                variables['groups']  = dict()
                for (group_name, group) in iteritems(self._inventory.groups):
                    variables['groups'][group_name] = [h.name for h in group.get_hosts()]
        if play:
            variables['role_names'] = [r._role_name for r in play.roles]

        if task:
            if task._role:
                variables['role_name'] = task._role.get_name()
                variables['role_path'] = task._role._role_path
                variables['role_uuid'] = text_type(task._role._uuid)

        if self._inventory is not None:
            variables['inventory_dir'] = self._inventory.basedir()
            variables['inventory_file'] = self._inventory.src()
            if play:
                # add the list of hosts in the play, as adjusted for limit/filters
                # DEPRECATED: play_hosts should be deprecated in favor of ansible_play_hosts,
                #             however this would take work in the templating engine, so for now
                #             we'll add both so we can give users something transitional to use
                host_list = [x.name for x in self._inventory.get_hosts()]
                variables['play_hosts'] = host_list
                variables['ansible_play_hosts'] = host_list

        # the 'omit' value alows params to be left out if the variable they are based on is undefined
        variables['omit'] = self._omit_token
        variables['ansible_version'] = CLI.version_info(gitinfo=False)

        return variables

    def _get_delegated_vars(self, loader, play, task, existing_variables):
        # we unfortunately need to template the delegate_to field here,
        # as we're fetching vars before post_validate has been called on
        # the task that has been passed in
        vars_copy = existing_variables.copy()
        templar = Templar(loader=loader, variables=vars_copy)

        items = []
        if task.loop is not None:
            if task.loop in lookup_loader:
                #TODO: remove convert_bare true and deprecate this in with_
                try:
                    loop_terms = listify_lookup_plugin_terms(terms=task.loop_args, templar=templar, loader=loader, fail_on_undefined=True, convert_bare=True)
                except AnsibleUndefinedVariable as e:
                    if 'has no attribute' in str(e):
                        loop_terms = []
                        display.deprecated("Skipping task due to undefined attribute, in the future this will be a fatal error.")
                    else:
                        raise
                items = lookup_loader.get(task.loop, loader=loader, templar=templar).run(terms=loop_terms, variables=vars_copy)
            else:
                raise AnsibleError("Unexpected failure in finding the lookup named '%s' in the available lookup plugins" % task.loop)
        else:
            items = [None]

        delegated_host_vars = dict()
        for item in items:
            # update the variables with the item value for templating, in case we need it
            if item is not None:
                vars_copy['item'] = item

            templar.set_available_variables(vars_copy)
            delegated_host_name = templar.template(task.delegate_to, fail_on_undefined=False)
            if delegated_host_name in delegated_host_vars:
                # no need to repeat ourselves, as the delegate_to value
                # does not appear to be tied to the loop item variable
                continue

            # a dictionary of variables to use if we have to create a new host below
            # we set the default port based on the default transport here, to make sure
            # we use the proper default for windows
            new_port = C.DEFAULT_REMOTE_PORT
            if C.DEFAULT_TRANSPORT == 'winrm':
                new_port = 5986

            new_delegated_host_vars = dict(
                ansible_host=delegated_host_name,
                ansible_port=new_port,
                ansible_user=C.DEFAULT_REMOTE_USER,
                ansible_connection=C.DEFAULT_TRANSPORT,
            )

            # now try to find the delegated-to host in inventory, or failing that,
            # create a new host on the fly so we can fetch variables for it
            delegated_host = None
            if self._inventory is not None:
                delegated_host = self._inventory.get_host(delegated_host_name)
                # try looking it up based on the address field, and finally
                # fall back to creating a host on the fly to use for the var lookup
                if delegated_host is None:
                    for h in self._inventory.get_hosts(ignore_limits_and_restrictions=True):
                        # check if the address matches, or if both the delegated_to host
                        # and the current host are in the list of localhost aliases
                        if h.address == delegated_host_name or h.name in C.LOCALHOST and delegated_host_name in C.LOCALHOST:
                            delegated_host = h
                            break
                    else:
                        delegated_host = Host(name=delegated_host_name)
                        delegated_host.vars.update(new_delegated_host_vars)
            else:
                delegated_host = Host(name=delegated_host_name)
                delegated_host.vars.update(new_delegated_host_vars)

            # now we go fetch the vars for the delegated-to host and save them in our
            # master dictionary of variables to be used later in the TaskExecutor/PlayContext
            delegated_host_vars[delegated_host_name] = self.get_vars(
                loader=loader,
                play=play,
                host=delegated_host,
                task=task,
                include_delegate_to=False,
                include_hostvars=False,
            )

        return delegated_host_vars

    def _get_inventory_basename(self, path):
        '''
        Returns the basename minus the extension of the given path, so the
        bare filename can be matched against host/group names later
        '''

        (name, ext) = os.path.splitext(os.path.basename(path))
        if ext not in ('.yml', '.yaml'):
            return os.path.basename(path)
        else:
            return name

    def _load_inventory_file(self, path, loader):
        '''
        helper function, which loads the file and gets the
        basename of the file without the extension
        '''

        if loader.is_directory(path):
            data = dict()

            try:
                names = loader.list_directory(path)
            except os.error as err:
                raise AnsibleError("This folder cannot be listed: %s: %s." % (path, err.strerror))

            # evaluate files in a stable order rather than whatever
            # order the filesystem lists them.
            names.sort()

            # do not parse hidden files or dirs, e.g. .svn/
            paths = [os.path.join(path, name) for name in names if not name.startswith('.')]
            for p in paths:
                _found, results = self._load_inventory_file(path=p, loader=loader)
                if results is not None:
                    data = combine_vars(data, results)

        else:
            file_name, ext = os.path.splitext(path)
            data = None
            if not ext or ext not in C.YAML_FILENAME_EXTENSIONS:
                for test_ext in C.YAML_FILENAME_EXTENSIONS:
                    new_path = path + test_ext
                    if loader.path_exists(new_path):
                        data = loader.load_from_file(new_path)
                        break
            else:
                if loader.path_exists(path):
                    data = loader.load_from_file(path)

        name = self._get_inventory_basename(path)
        return (name, data)

    def add_host_vars_file(self, path, loader):
        '''
        Loads and caches a host_vars file in the _host_vars_files dict,
        where the key to that dictionary is the basename of the file, minus
        the extension, for matching against a given inventory host name
        '''

        (name, data) = self._load_inventory_file(path, loader)
        if data:
            if name not in self._host_vars_files:
                self._host_vars_files[name] = []
            self._host_vars_files[name].append(data)
            return data
        else:
            return dict()

    def add_group_vars_file(self, path, loader):
        '''
        Loads and caches a host_vars file in the _host_vars_files dict,
        where the key to that dictionary is the basename of the file, minus
        the extension, for matching against a given inventory host name
        '''

        (name, data) = self._load_inventory_file(path, loader)
        if data:
            if name not in self._group_vars_files:
                self._group_vars_files[name] = []
            self._group_vars_files[name].append(data)
            return data
        else:
            return dict()

    def set_host_facts(self, host, facts):
        '''
        Sets or updates the given facts for a host in the fact cache.
        '''

        assert isinstance(facts, dict)

        if host.name not in self._fact_cache:
            self._fact_cache[host.name] = facts
        else:
            try:
                self._fact_cache.update(host.name, facts)
            except KeyError:
                self._fact_cache[host.name] = facts

    def set_nonpersistent_facts(self, host, facts):
        '''
        Sets or updates the given facts for a host in the fact cache.
        '''

        assert isinstance(facts, dict)

        if host.name not in self._nonpersistent_fact_cache:
            self._nonpersistent_fact_cache[host.name] = facts
        else:
            try:
                self._nonpersistent_fact_cache[host.name].update(facts)
            except KeyError:
                self._nonpersistent_fact_cache[host.name] = facts

    def set_host_variable(self, host, varname, value):
        '''
        Sets a value in the vars_cache for a host.
        '''
        host_name = host.get_name()
        if host_name not in self._vars_cache:
            self._vars_cache[host_name] = dict()
        if varname in self._vars_cache[host_name]:
            self._vars_cache[host_name][varname] = combine_vars(self._vars_cache[host_name][varname], value)
        else:
            self._vars_cache[host_name][varname] = value
