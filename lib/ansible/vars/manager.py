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

from collections import defaultdict

try:
    from hashlib import sha1
except ImportError:
    from sha import sha as sha1

from jinja2.exceptions import UndefinedError

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleParserError, AnsibleUndefinedVariable, AnsibleFileNotFound, AnsibleAssertionError, AnsibleTemplateError
from ansible.inventory.host import Host
from ansible.inventory.helpers import sort_groups, get_group_vars
from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.common._collections_compat import Mapping, MutableMapping, Sequence
from ansible.module_utils.six import iteritems, text_type, string_types
from ansible.plugins.loader import lookup_loader, vars_loader
from ansible.vars.fact_cache import FactCache
from ansible.template import Templar
from ansible.utils.display import Display
from ansible.utils.listify import listify_lookup_plugin_terms
from ansible.utils.vars import combine_vars, load_extra_vars, load_options_vars
from ansible.utils.unsafe_proxy import wrap_var
from ansible.vars.clean import namespace_facts, clean_facts

display = Display()


def preprocess_vars(a):
    '''
    Ensures that vars contained in the parameter passed in are
    returned as a list of dictionaries, to ensure for instance
    that vars loaded from a file conform to an expected state.
    '''

    if a is None:
        return None
    elif not isinstance(a, list):
        data = [a]
    else:
        data = a

    for item in data:
        if not isinstance(item, MutableMapping):
            raise AnsibleError("variable files must contain either a dictionary of variables, or a list of dictionaries. Got: %s (%s)" % (a, type(a)))

    return data


class VariableManager:

    _ALLOWED = frozenset(['plugins_by_group', 'groups_plugins_play', 'groups_plugins_inventory', 'groups_inventory',
                          'all_plugins_play', 'all_plugins_inventory', 'all_inventory'])

    def __init__(self, loader=None, inventory=None, version_info=None):
        self._nonpersistent_fact_cache = defaultdict(dict)
        self._vars_cache = defaultdict(dict)
        self._extra_vars = defaultdict(dict)
        self._host_vars_files = defaultdict(dict)
        self._group_vars_files = defaultdict(dict)
        self._inventory = inventory
        self._loader = loader
        self._hostvars = None
        self._omit_token = '__omit_place_holder__%s' % sha1(os.urandom(64)).hexdigest()

        self._options_vars = load_options_vars(version_info)

        # If the basedir is specified as the empty string then it results in cwd being used.
        # This is not a safe location to load vars from.
        basedir = self._options_vars.get('basedir', False)
        self.safe_basedir = bool(basedir is False or basedir)

        # load extra vars
        self._extra_vars = load_extra_vars(loader=self._loader)

        # load fact cache
        try:
            self._fact_cache = FactCache()
        except AnsibleError as e:
            # bad cache plugin is not fatal error
            # fallback to a dict as in memory cache
            display.warning(to_text(e))
            self._fact_cache = {}

    def __getstate__(self):
        data = dict(
            fact_cache=self._fact_cache,
            np_fact_cache=self._nonpersistent_fact_cache,
            vars_cache=self._vars_cache,
            extra_vars=self._extra_vars,
            host_vars_files=self._host_vars_files,
            group_vars_files=self._group_vars_files,
            omit_token=self._omit_token,
            options_vars=self._options_vars,
            inventory=self._inventory,
            safe_basedir=self.safe_basedir,
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
        self.safe_basedir = data.get('safe_basedir', False)

    @property
    def extra_vars(self):
        return self._extra_vars

    def set_inventory(self, inventory):
        self._inventory = inventory

    def get_vars(self, play=None, host=None, task=None, include_hostvars=True, include_delegate_to=True, use_cache=True,
                 _hosts=None, _hosts_all=None):
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

        ``_hosts`` and ``_hosts_all`` should be considered private args, with only internal trusted callers relying
        on the functionality they provide. These arguments may be removed at a later date without a deprecation
        period and without warning.
        '''

        display.debug("in VariableManager get_vars()")

        all_vars = dict()
        magic_variables = self._get_magic_variables(
            play=play,
            host=host,
            task=task,
            include_hostvars=include_hostvars,
            include_delegate_to=include_delegate_to,
            _hosts=_hosts,
            _hosts_all=_hosts_all,
        )

        # default for all cases
        basedirs = []
        if self.safe_basedir:  # avoid adhoc/console loading cwd
            basedirs = [self._loader.get_basedir()]

        if play:
            # first we compile any vars specified in defaults/main.yml
            # for all roles within the specified play
            for role in play.get_roles():
                all_vars = combine_vars(all_vars, role.get_default_vars())

        if task:
            # set basedirs
            if C.PLAYBOOK_VARS_ROOT == 'all':  # should be default
                basedirs = task.get_search_path()
            elif C.PLAYBOOK_VARS_ROOT in ('bottom', 'playbook_dir'):  # only option in 2.4.0
                basedirs = [task.get_search_path()[0]]
            elif C.PLAYBOOK_VARS_ROOT != 'top':
                # preserves default basedirs, only option pre 2.3
                raise AnsibleError('Unknown playbook vars logic: %s' % C.PLAYBOOK_VARS_ROOT)

            # if we have a task in this context, and that task has a role, make
            # sure it sees its defaults above any other roles, as we previously
            # (v1) made sure each task had a copy of its roles default vars
            if task._role is not None and (play or task.action in C._ACTION_INCLUDE_ROLE):
                all_vars = combine_vars(all_vars, task._role.get_default_vars(dep_chain=task.get_dep_chain()))

        if host:
            # THE 'all' group and the rest of groups for a host, used below
            all_group = self._inventory.groups.get('all')
            host_groups = sort_groups([g for g in host.get_groups() if g.name not in ['all']])

            def _get_plugin_vars(plugin, path, entities):
                data = {}
                try:
                    data = plugin.get_vars(self._loader, path, entities)
                except AttributeError:
                    try:
                        for entity in entities:
                            if isinstance(entity, Host):
                                data.update(plugin.get_host_vars(entity.name))
                            else:
                                data.update(plugin.get_group_vars(entity.name))
                    except AttributeError:
                        if hasattr(plugin, 'run'):
                            raise AnsibleError("Cannot use v1 type vars plugin %s from %s" % (plugin._load_name, plugin._original_path))
                        else:
                            raise AnsibleError("Invalid vars plugin %s from %s" % (plugin._load_name, plugin._original_path))
                return data

            # internal fuctions that actually do the work
            def _plugins_inventory(entities):
                ''' merges all entities by inventory source '''
                data = {}
                for inventory_dir in self._inventory._sources:
                    if ',' in inventory_dir and not os.path.exists(inventory_dir):  # skip host lists
                        continue
                    elif not os.path.isdir(to_bytes(inventory_dir)):  # always pass 'inventory directory'
                        inventory_dir = os.path.dirname(inventory_dir)

                    for plugin in vars_loader.all():

                        data = combine_vars(data, _get_plugin_vars(plugin, inventory_dir, entities))
                return data

            def _plugins_play(entities):
                ''' merges all entities adjacent to play '''
                data = {}
                for plugin in vars_loader.all():

                    for path in basedirs:
                        data = combine_vars(data, _get_plugin_vars(plugin, path, entities))
                return data

            # configurable functions that are sortable via config, rememer to add to _ALLOWED if expanding this list
            def all_inventory():
                return all_group.get_vars()

            def all_plugins_inventory():
                return _plugins_inventory([all_group])

            def all_plugins_play():
                return _plugins_play([all_group])

            def groups_inventory():
                ''' gets group vars from inventory '''
                return get_group_vars(host_groups)

            def groups_plugins_inventory():
                ''' gets plugin sources from inventory for groups '''
                return _plugins_inventory(host_groups)

            def groups_plugins_play():
                ''' gets plugin sources from play for groups '''
                return _plugins_play(host_groups)

            def plugins_by_groups():
                '''
                    merges all plugin sources by group,
                    This should be used instead, NOT in combination with the other groups_plugins* functions
                '''
                data = {}
                for group in host_groups:
                    data[group] = combine_vars(data[group], _plugins_inventory(group))
                    data[group] = combine_vars(data[group], _plugins_play(group))
                return data

            # Merge groups as per precedence config
            # only allow to call the functions we want exposed
            for entry in C.VARIABLE_PRECEDENCE:
                if entry in self._ALLOWED:
                    display.debug('Calling %s to load vars for %s' % (entry, host.name))
                    all_vars = combine_vars(all_vars, locals()[entry]())
                else:
                    display.warning('Ignoring unknown variable precedence entry: %s' % (entry))

            # host vars, from inventory, inventory adjacent and play adjacent via plugins
            all_vars = combine_vars(all_vars, host.get_vars())
            all_vars = combine_vars(all_vars, _plugins_inventory([host]))
            all_vars = combine_vars(all_vars, _plugins_play([host]))

            # finally, the facts caches for this host, if it exists
            # TODO: cleaning of facts should eventually become part of taskresults instead of vars
            try:
                facts = wrap_var(self._fact_cache.get(host.name, {}))
                all_vars.update(namespace_facts(facts))

                # push facts to main namespace
                if C.INJECT_FACTS_AS_VARS:
                    all_vars = combine_vars(all_vars, wrap_var(clean_facts(facts)))
                else:
                    # always 'promote' ansible_local
                    all_vars = combine_vars(all_vars, wrap_var({'ansible_local': facts.get('ansible_local', {})}))
            except KeyError:
                pass

        if play:
            all_vars = combine_vars(all_vars, play.get_vars())

            vars_files = play.get_vars_files()
            try:
                for vars_file_item in vars_files:
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
                            if not (isinstance(vars_file, Sequence)):
                                raise AnsibleError(
                                    "Invalid vars_files entry found: %r\n"
                                    "vars_files entries should be either a string type or "
                                    "a list of string types after template expansion" % vars_file
                                )
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
                            raise AnsibleUndefinedVariable("an undefined variable was found when attempting to template the vars_files item '%s'"
                                                           % vars_file_item, obj=vars_file_item)
                        else:
                            # we do not have a full context here, and the missing variable could be because of that
                            # so just show a warning and continue
                            display.vvv("skipping vars_file '%s' due to an undefined variable" % vars_file_item)
                            continue

                    display.vvv("Read vars_file '%s'" % vars_file_item)
            except TypeError:
                raise AnsibleParserError("Error while reading vars files - please supply a list of file names. "
                                         "Got '%s' of type %s" % (vars_files, type(vars_files)))

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
            # include_vars non-persistent cache
            all_vars = combine_vars(all_vars, self._vars_cache.get(host.get_name(), dict()))
            # fact non-persistent cache
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
            all_vars['ansible_delegated_vars'], all_vars['_ansible_loop_cache'] = self._get_delegated_vars(play, task, all_vars)

        # 'vars' magic var
        if task or play:
            # has to be copy, otherwise recursive ref
            all_vars['vars'] = all_vars.copy()

        display.debug("done with get_vars()")
        return all_vars

    def _get_magic_variables(self, play, host, task, include_hostvars, include_delegate_to,
                             _hosts=None, _hosts_all=None):
        '''
        Returns a dictionary of so-called "magic" variables in Ansible,
        which are special variables we set internally for use.
        '''

        variables = {}
        variables['playbook_dir'] = os.path.abspath(self._loader.get_basedir())
        variables['ansible_playbook_python'] = sys.executable

        if play:
            # This is a list of all role names of all dependencies for all roles for this play
            dependency_role_names = list(set([d.get_name() for r in play.roles for d in r.get_all_dependencies()]))
            # This is a list of all role names of all roles for this play
            play_role_names = [r.get_name() for r in play.roles]

            # ansible_role_names includes all role names, dependent or directly referenced by the play
            variables['ansible_role_names'] = list(set(dependency_role_names + play_role_names))
            # ansible_play_role_names includes the names of all roles directly referenced by this play
            # roles that are implicitly referenced via dependencies are not listed.
            variables['ansible_play_role_names'] = play_role_names
            # ansible_dependent_role_names includes the names of all roles that are referenced via dependencies
            # dependencies that are also explicitly named as roles are included in this list
            variables['ansible_dependent_role_names'] = dependency_role_names

            # DEPRECATED: role_names should be deprecated in favor of ansible_role_names or ansible_play_role_names
            variables['role_names'] = variables['ansible_play_role_names']

            variables['ansible_play_name'] = play.get_name()

        if task:
            if task._role:
                variables['role_name'] = task._role.get_name(include_role_fqcn=False)
                variables['role_path'] = task._role._role_path
                variables['role_uuid'] = text_type(task._role._uuid)
                variables['ansible_collection_name'] = task._role._role_collection
                variables['ansible_role_name'] = task._role.get_name()

        if self._inventory is not None:
            variables['groups'] = self._inventory.get_groups_dict()
            if play:
                templar = Templar(loader=self._loader)
                if templar.is_template(play.hosts):
                    pattern = 'all'
                else:
                    pattern = play.hosts or 'all'
                # add the list of hosts in the play, as adjusted for limit/filters
                if not _hosts_all:
                    _hosts_all = [h.name for h in self._inventory.get_hosts(pattern=pattern, ignore_restrictions=True)]
                if not _hosts:
                    _hosts = [h.name for h in self._inventory.get_hosts()]

                variables['ansible_play_hosts_all'] = _hosts_all[:]
                variables['ansible_play_hosts'] = [x for x in variables['ansible_play_hosts_all'] if x not in play._removed_hosts]
                variables['ansible_play_batch'] = [x for x in _hosts if x not in play._removed_hosts]

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
        if not hasattr(task, 'loop'):
            # This "task" is not a Task, so we need to skip it
            return {}, None

        # we unfortunately need to template the delegate_to field here,
        # as we're fetching vars before post_validate has been called on
        # the task that has been passed in
        vars_copy = existing_variables.copy()
        templar = Templar(loader=self._loader, variables=vars_copy)

        items = []
        has_loop = True
        if task.loop_with is not None:
            if task.loop_with in lookup_loader:
                try:
                    loop_terms = listify_lookup_plugin_terms(terms=task.loop, templar=templar,
                                                             loader=self._loader, fail_on_undefined=True, convert_bare=False)
                    items = wrap_var(lookup_loader.get(task.loop_with, loader=self._loader, templar=templar).run(terms=loop_terms, variables=vars_copy))
                except AnsibleTemplateError:
                    # This task will be skipped later due to this, so we just setup
                    # a dummy array for the later code so it doesn't fail
                    items = [None]
            else:
                raise AnsibleError("Failed to find the lookup named '%s' in the available lookup plugins" % task.loop_with)
        elif task.loop is not None:
            try:
                items = templar.template(task.loop)
            except AnsibleTemplateError:
                # This task will be skipped later due to this, so we just setup
                # a dummy array for the later code so it doesn't fail
                items = [None]
        else:
            has_loop = False
            items = [None]

        # since host can change per loop, we keep dict per host name resolved
        delegated_host_vars = dict()
        item_var = getattr(task.loop_control, 'loop_var', 'item')
        cache_items = False
        for item in items:
            # update the variables with the item value for templating, in case we need it
            if item is not None:
                vars_copy[item_var] = item

            templar.available_variables = vars_copy
            delegated_host_name = templar.template(task.delegate_to, fail_on_undefined=False)
            if delegated_host_name != task.delegate_to:
                cache_items = True
            if delegated_host_name is None:
                raise AnsibleError(message="Undefined delegate_to host for task:", obj=task._ds)
            if not isinstance(delegated_host_name, string_types):
                raise AnsibleError(message="the field 'delegate_to' has an invalid type (%s), and could not be"
                                           " converted to a string type." % type(delegated_host_name), obj=task._ds)

            if delegated_host_name in delegated_host_vars:
                # no need to repeat ourselves, as the delegate_to value
                # does not appear to be tied to the loop item variable
                continue

            # now try to find the delegated-to host in inventory, or failing that,
            # create a new host on the fly so we can fetch variables for it
            delegated_host = None
            if self._inventory is not None:
                delegated_host = self._inventory.get_host(delegated_host_name)
                # try looking it up based on the address field, and finally
                # fall back to creating a host on the fly to use for the var lookup
                if delegated_host is None:
                    for h in self._inventory.get_hosts(ignore_limits=True, ignore_restrictions=True):
                        # check if the address matches, or if both the delegated_to host
                        # and the current host are in the list of localhost aliases
                        if h.address == delegated_host_name:
                            delegated_host = h
                            break
                    else:
                        delegated_host = Host(name=delegated_host_name)
            else:
                delegated_host = Host(name=delegated_host_name)

            # now we go fetch the vars for the delegated-to host and save them in our
            # master dictionary of variables to be used later in the TaskExecutor/PlayContext
            delegated_host_vars[delegated_host_name] = self.get_vars(
                play=play,
                host=delegated_host,
                task=task,
                include_delegate_to=False,
                include_hostvars=True,
            )
            delegated_host_vars[delegated_host_name]['inventory_hostname'] = vars_copy.get('inventory_hostname')

        _ansible_loop_cache = None
        if has_loop and cache_items:
            # delegate_to templating produced a change, so we will cache the templated items
            # in a special private hostvar
            # this ensures that delegate_to+loop doesn't produce different results than TaskExecutor
            # which may reprocess the loop
            _ansible_loop_cache = items

        return delegated_host_vars, _ansible_loop_cache

    def clear_facts(self, hostname):
        '''
        Clears the facts for a host
        '''
        self._fact_cache.pop(hostname, None)

    def set_host_facts(self, host, facts):
        '''
        Sets or updates the given facts for a host in the fact cache.
        '''

        if not isinstance(facts, Mapping):
            raise AnsibleAssertionError("the type of 'facts' to set for host_facts should be a Mapping but is a %s" % type(facts))

        try:
            host_cache = self._fact_cache[host]
        except KeyError:
            # We get to set this as new
            host_cache = facts
        else:
            if not isinstance(host_cache, MutableMapping):
                raise TypeError('The object retrieved for {0} must be a MutableMapping but was'
                                ' a {1}'.format(host, type(host_cache)))
            # Update the existing facts
            host_cache.update(facts)

        # Save the facts back to the backing store
        self._fact_cache[host] = host_cache

    def set_nonpersistent_facts(self, host, facts):
        '''
        Sets or updates the given facts for a host in the fact cache.
        '''

        if not isinstance(facts, Mapping):
            raise AnsibleAssertionError("the type of 'facts' to set for nonpersistent_facts should be a Mapping but is a %s" % type(facts))

        try:
            self._nonpersistent_fact_cache[host].update(facts)
        except KeyError:
            self._nonpersistent_fact_cache[host] = facts

    def set_host_variable(self, host, varname, value):
        '''
        Sets a value in the vars_cache for a host.
        '''
        if host not in self._vars_cache:
            self._vars_cache[host] = dict()
        if varname in self._vars_cache[host] and isinstance(self._vars_cache[host][varname], MutableMapping) and isinstance(value, MutableMapping):
            self._vars_cache[host] = combine_vars(self._vars_cache[host], {varname: value})
        else:
            self._vars_cache[host][varname] = value
