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
import sys

from collections import defaultdict, MutableMapping

try:
    from hashlib import sha1
except ImportError:
    from sha import sha as sha1

from jinja2.exceptions import UndefinedError

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleParserError, AnsibleUndefinedVariable, AnsibleFileNotFound
from ansible.inventory.host import Host
from ansible.module_utils.six import iteritems, string_types, text_type
from ansible.plugins import lookup_loader
from ansible.plugins.cache import FactCache
from ansible.template import Templar
from ansible.utils.listify import listify_lookup_plugin_terms
from ansible.utils.vars import combine_vars
from ansible.utils.unsafe_proxy import wrap_var
from ansible.module_utils._text import to_native

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


VARIABLE_CACHE = {}


class AnsibleInventory(object):
    ''' mock inventory group '''
    def __init__(self):
        self.groups = {}
        self.hosts = {}

class AnsibleInventoryObject(object):
    ''' class to hold data not in inventory '''
    def __init__(self):
        self.vars = {}

    def load_data(self, data):
        data = preprocess_vars(data)
        for item in data:
            self.vars = combine_vars(self.vars, item)

    def get_vars(self, include_file_data=True):
        return self.vars

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
        elif isinstance(dirty[k], dict):
            clean[k] = strip_internal_keys(dirty[k])
    return clean


class VariableManager:

    def __init__(self, loader=None, inventory=None):

        self._nonpersistent_fact_cache = defaultdict(dict)
        self._vars_cache = defaultdict(dict)
        self._extra_vars = defaultdict(dict)
        self._host_vars_files = defaultdict(dict)
        self._group_vars_files = defaultdict(dict)
        self._inventory = inventory
        self._loader = loader
        self._hostvars = None
        self._omit_token = '__omit_place_holder__%s' % sha1(os.urandom(64)).hexdigest()
        self._options_vars = defaultdict(dict)

        # bad cache plugin is not fatal error
        try:
            self._fact_cache = FactCache()
        except AnsibleError as e:
            display.warning(to_native(e))
            # fallback to a dict as in memory cache
            self._fact_cache = {}

    def __getstate__(self):
        data = dict(
            fact_cache = self._fact_cache,
            np_fact_cache = self._nonpersistent_fact_cache,
            vars_cache = self._vars_cache,
            extra_vars = self._extra_vars,
            host_vars_files = self._host_vars_files,
            group_vars_files = self._group_vars_files,
            omit_token = self._omit_token,
            options_vars = self._options_vars,
            inventory = self._inventory,
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
        self._options_vars = data.get('options_vars', dict())

    def _get_cache_entry(self, play=None, host=None, task=None):
        play_id = host_id = task_id = "NONE"
        if play:
            play_id = play._uuid
        if host:
            host_id = host.get_name()
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

    @property
    def options_vars(self):
        ''' ensures a clean copy of the options_vars are made '''
        return self._options_vars.copy()

    @options_vars.setter
    def options_vars(self, value):
        ''' ensures a clean copy of the options_vars are used to set the value '''
        assert isinstance(value, dict)
        self._options_vars = value.copy()

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

    def get_vars(self, play=None, host=None, task=None, include_hostvars=True, include_delegate_to=True, use_cache=True):
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

        display.debug("in VariableManager get_vars()")
        cache_entry = self._get_cache_entry(play=play, host=host, task=task)
        if cache_entry in VARIABLE_CACHE and use_cache:
            display.debug("vars are cached, returning them now")
            return VARIABLE_CACHE[cache_entry]

        all_vars = dict()
        magic_variables = self._get_magic_variables(
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
        if task and task._role is not None and (play or task.action == 'include_role'):
            all_vars = combine_vars(all_vars, task._role.get_default_vars(dep_chain=task.get_dep_chain()))

        if host:
            ### INIT WORK (use unsafe as we are going to copy/merge vars, no need to x2 copy)
            # loader basedir
            basedir = self._loader.get_basedir()

            # load host vars if needed (datalaoder keeps cache)
            if not host.name in self._host_vars_files:
                self._host_vars_files[host.name] = AnsibleInventoryObject()
            self._loader.load_vars_files(self._host_vars_files, os.path.join(basedir, 'host_vars'), unsafe=True)

            # load group vars if needed (dataloader keeps cache)
            for group in host.get_groups():
                if group.name not in self._group_vars_files:
                    self._group_vars_files[group.name] = AnsibleInventoryObject()
            self._loader.load_vars_files(self._group_vars_files, os.path.join(basedir, 'group_vars'), unsafe=True)

            ### START MERGING
            if C.SOURCE_OVER_GROUPS:

                # all from inventory
                all_vars = combine_vars(all_vars, self._inventory.groups['all'].get_vars(include_file_data=False))

                # groups from inventory
                for group in sorted(host.get_groups(), key=lambda g: (g.depth, g.priority, g.name)):
                    if group.name != 'all':
                        all_vars = combine_vars(all_vars, self._inventory.groups[group.name].get_vars(include_file_data=False))

                # 'all' inventory group_vars
                all_vars = combine_vars(all_vars, self._inventory.groups['all'].get_file_vars())

                # 'all' play group_vars
                if 'all' in self._group_vars_files:
                    all_vars = combine_vars(all_vars, self._group_vars_files['all'].vars)

                # inventory group_vars
                for group in sorted(host.get_groups(), key=lambda g: (g.depth, g.priority, g.name)):
                    # all is special and process separately
                    if group.name != 'all':
                        all_vars = combine_vars(all_vars, self._inventory.groups[group.name].get_file_vars())

                # play group_vars files from pb
                for group in sorted(host.get_groups(), key=lambda g: (g.depth, g.priority, g.name)):
                    # all is special and process separately
                    if group.name != 'all' and group.name in self._group_vars_files:
                        # play group_vars
                        all_vars = combine_vars(all_vars, self._group_vars_files[group.name].vars)
            else:
                # go over groups following hierarchy over source
                seen = set()
                mygroups = host.get_groups()
                def _merge_group_vars(myvars, group):
                    if group.name not in seen and group in mygroups:
                        seen.add(group.name)
                        myvars = combine_vars(myvars, self._inventory.groups[group.name].vars)
                        if group.name in self._group_vars_files:
                            # play group_vars
                            myvars = combine_vars(myvars, self._group_vars_files[group.name].vars)
                        for cgroup in sorted(group.child_groups, key=lambda g: (g.depth, g.priority, g.name)):
                            _merge_group_vars(myvars, cgroup)

                _merge_group_vars(all_vars, self._inventory.groups['all'])

            # now we merge in host vars from the inventory host (includes host_vars already)
            all_vars = combine_vars(all_vars, host.vars)

            # now play host_vars
            if host.name in self._host_vars_files:
                all_vars = combine_vars(all_vars, self._host_vars_files[host.name].vars)

            # finally, the facts caches for this host, if it exists
            try:
                host_facts = wrap_var(self._fact_cache.get(host.name, dict()))
                if not C.NAMESPACE_FACTS:
                    # allow facts to polute main namespace
                    all_vars = combine_vars(all_vars, host_facts)
                # always return namespaced facts
                all_vars = combine_vars(all_vars, {'ansible_facts': host_facts})
            except KeyError:
                pass

        if play:
            all_vars = combine_vars(all_vars, play.get_vars())

            for vars_file_item in play.get_vars_files():
                # create a set of temporary vars here, which incorporate the extra
                # and magic vars so we can properly template the vars_files entries
                temp_vars = combine_vars(all_vars, self._extra_vars)
                temp_vars = combine_vars(temp_vars, magic_variables)
                templar = Templar(loader=self._loader, variables=temp_vars)

                # we assume each item in the list is itself a list, as we
                # support "conditional includes" for vars_files, which mimics
                # the with_first_found mechanism.
                vars_file_list = vars_file_item
                if not isinstance(vars_file_list, list):
                    vars_file_list = [vars_file_list]

                # now we iterate through the (potential) files, and break out
                # as soon as we read one from the list. If none are found, we
                # raise an error, which is silently ignored at this point.
                try:
                    for vars_file in vars_file_list:
                        vars_file = templar.template(vars_file)
                        try:
                            data = preprocess_vars(self._loader.load_from_file(vars_file, unsafe=True))
                            if data is not None:
                                for item in data:
                                    all_vars = combine_vars(all_vars, item)
                            break
                        except AnsibleFileNotFound:
                            # we continue on loader failures
                            continue
                        except AnsibleParserError:
                            raise
                    else:
                        # if include_delegate_to is set to False, we ignore the missing
                        # vars file here because we're working on a delegated host
                        if include_delegate_to:
                            raise AnsibleFileNotFound("vars file %s was not found" % vars_file_item)
                except (UndefinedError, AnsibleUndefinedVariable):
                    if host is not None and self._fact_cache.get(host.name, dict()).get('module_setup') and task is not None:
                        raise AnsibleUndefinedVariable("an undefined variable was found when attempting to template the vars_files item '%s'" % vars_file_item,
                                                       obj=vars_file_item)
                    else:
                        # we do not have a full context here, and the missing variable could be
                        # because of that, so just show a warning and continue
                        display.vvv("skipping vars_file '%s' due to an undefined variable" % vars_file_item)
                        continue

            # By default, we now merge in all vars from all roles in the play,
            # unless the user has disabled this via a config option
            if not C.DEFAULT_PRIVATE_ROLE_VARS:
                for role in play.get_roles():
                    all_vars = combine_vars(all_vars, role.get_vars(include_params=False))

        # next, we merge in the vars from the role, which will specifically
        # follow the role dependency chain, and then we merge in the tasks
        # vars (which will look at parent blocks/task includes)
        if task:
            if task._role:
                all_vars = combine_vars(all_vars, task._role.get_vars(task.get_dep_chain(), include_params=False))
            all_vars = combine_vars(all_vars, task.get_vars())

        # next, we merge in the vars cache (include vars) and nonpersistent
        # facts cache (set_fact/register), in that order
        if host:
            all_vars = combine_vars(all_vars, self._vars_cache.get(host.get_name(), dict()))
            all_vars = combine_vars(all_vars, self._nonpersistent_fact_cache.get(host.name, dict()))

        # next, we merge in role params and task include params
        if task:
            if task._role:
                all_vars = combine_vars(all_vars, task._role.get_role_params(task.get_dep_chain()))

            # special case for include tasks, where the include params
            # may be specified in the vars field for the task, which should
            # have higher precedence than the vars/np facts above
            all_vars = combine_vars(all_vars, task.get_include_params())

        # extra vars
        all_vars = combine_vars(all_vars, self._extra_vars)

        # magic variables
        all_vars = combine_vars(all_vars, magic_variables)

        # special case for the 'environment' magic variable, as someone
        # may have set it as a variable and we don't want to stomp on it
        if task:
            all_vars['environment'] = task.environment

        # if we have a task and we're delegating to another host, figure out the
        # variables for that host now so we don't have to rely on hostvars later
        if task and task.delegate_to is not None and include_delegate_to:
            all_vars['ansible_delegated_vars'] = self._get_delegated_vars(play, task, all_vars)

        # 'vars' magic var
        if task or play:
            # has to be copy, otherwise recursive ref
            all_vars['vars'] = all_vars.copy()

        display.debug("done with get_vars()")
        return all_vars

    def _get_magic_variables(self, play, host, task, include_hostvars, include_delegate_to):
        '''
        Returns a dictionary of so-called "magic" variables in Ansible,
        which are special variables we set internally for use.
        '''

        variables = {}
        variables['playbook_dir'] = os.path.abspath(self._loader.get_basedir())
        variables['ansible_playbook_python'] = sys.executable

        if host:
            # host already provides some magic vars via host.get_vars()
            if self._inventory:
                variables['groups']  = self._inventory.get_groups_dict()
        if play:
            variables['role_names'] = [r._role_name for r in play.roles]

        if task:
            if task._role:
                variables['role_name'] = task._role.get_name()
                variables['role_path'] = task._role._role_path
                variables['role_uuid'] = text_type(task._role._uuid)

        if self._inventory is not None:
            if play:
                templar = Templar(loader=self._loader)
                if templar.is_template(play.hosts):
                    pattern = 'all'
                else:
                    pattern = play.hosts or 'all'
                # add the list of hosts in the play, as adjusted for limit/filters
                variables['ansible_play_hosts_all'] = [x.name for x in self._inventory.get_hosts(pattern=pattern, ignore_restrictions=True)]
                variables['ansible_play_hosts'] = [x for x in variables['ansible_play_hosts_all'] if x not in play._removed_hosts]
                variables['ansible_play_batch'] = [x.name for x in self._inventory.get_hosts() if x.name not in play._removed_hosts]

                # DEPRECATED: play_hosts should be deprecated in favor of ansible_play_batch,
                # however this would take work in the templating engine, so for now we'll add both
                variables['play_hosts'] = variables['ansible_play_batch']

        # the 'omit' value alows params to be left out if the variable they are based on is undefined
        variables['omit'] = self._omit_token
        # Set options vars
        for option, option_value in iteritems(self._options_vars):
            variables[option] = option_value

        if self._hostvars is not None and include_hostvars:
            variables['hostvars'] = self._hostvars

        return variables

    def _get_delegated_vars(self, play, task, existing_variables):
        # we unfortunately need to template the delegate_to field here,
        # as we're fetching vars before post_validate has been called on
        # the task that has been passed in
        vars_copy = existing_variables.copy()
        templar = Templar(loader=self._loader, variables=vars_copy)

        items = []
        if task.loop is not None:
            if task.loop in lookup_loader:
                try:
                    loop_terms = listify_lookup_plugin_terms(terms=task.loop_args, templar=templar,
                                                             loader=self._loader, fail_on_undefined=True, convert_bare=False)
                    items = lookup_loader.get(task.loop, loader=self._loader, templar=templar).run(terms=loop_terms, variables=vars_copy)
                except AnsibleUndefinedVariable:
                    # This task will be skipped later due to this, so we just setup
                    # a dummy array for the later code so it doesn't fail
                    items = [None]
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
            if delegated_host_name is None:
                raise AnsibleError(message="Undefined delegate_to host for task:", obj=task._ds)
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
                    if delegated_host_name in C.LOCALHOST:
                        delegated_host = self._inventory.localhost
                    else:
                        for h in self._inventory.get_hosts(ignore_limits=True, ignore_restrictions=True):
                            # check if the address matches, or if both the delegated_to host
                            # and the current host are in the list of localhost aliases
                            if h.address == delegated_host_name:
                                delegated_host = h
                                break
                        else:
                            delegated_host = Host(name=delegated_host_name)
                            delegated_host.load_data(new_delegated_host_vars)
            else:
                delegated_host = Host(name=delegated_host_name)
                delegated_host.load_data(new_delegated_host_vars)

            # now we go fetch the vars for the delegated-to host and save them in our
            # master dictionary of variables to be used later in the TaskExecutor/PlayContext
            delegated_host_vars[delegated_host_name] = self.get_vars(
                play=play,
                host=delegated_host,
                task=task,
                include_delegate_to=False,
                include_hostvars=False,
            )
        return delegated_host_vars

    def clear_facts(self, hostname):
        '''
        Clears the facts for a host
        '''
        if hostname in self._fact_cache:
            del self._fact_cache[hostname]

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
        if varname in self._vars_cache[host_name] and isinstance(self._vars_cache[host_name][varname], MutableMapping) and isinstance(value, MutableMapping):
            self._vars_cache[host_name] = combine_vars(self._vars_cache[host_name], {varname: value})
        else:
            self._vars_cache[host_name][varname] = value
