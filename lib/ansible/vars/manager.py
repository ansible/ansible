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

from __future__ import annotations

import os
import sys
import typing as t

from collections import defaultdict
from collections.abc import Mapping, MutableMapping

from ansible import constants as C
from ansible.module_utils._internal import _deprecator
from ansible.module_utils._internal._datatag import _tags
from ansible.errors import (AnsibleError, AnsibleParserError, AnsibleUndefinedVariable, AnsibleFileNotFound,
                            AnsibleAssertionError, AnsibleValueOmittedError)
from ansible.inventory.host import Host
from ansible.inventory.helpers import sort_groups, get_group_vars
from ansible.inventory.manager import InventoryManager
from ansible.module_utils.datatag import native_type_name
from ansible.module_utils.six import text_type
from ansible.parsing.dataloader import DataLoader
from ansible._internal._templating._engine import TemplateEngine
from ansible.plugins.loader import cache_loader
from ansible.utils.display import Display
from ansible.utils.vars import combine_vars, load_extra_vars, load_options_vars
from ansible.vars.clean import namespace_facts, clean_facts
from ansible.vars.hostvars import HostVars
from ansible.vars.plugins import get_vars_from_inventory_sources, get_vars_from_path
from ansible.vars.reserved import warn_if_reserved

if t.TYPE_CHECKING:
    from ansible.playbook import Play
    from ansible.playbook.task import Task

display = Display()

# deprecated: description='enable top-level facts deprecation' core_version='2.20'
# _DEPRECATE_TOP_LEVEL_FACT_TAG = _tags.Deprecated(
#     msg='Top-level facts are deprecated.',
#     version='2.24',
#     deprecator=_deprecator.ANSIBLE_CORE_DEPRECATOR,
#     help_text='Use `ansible_facts` instead.',
# )


def _deprecate_top_level_fact(value: t.Any) -> t.Any:
    """
    Deprecate the given top-level fact value.
    The inner values are shared to aid in message de-duplication across hosts/values, and reduce intra-process memory usage.
    Unique tag instances are required to achieve the correct de-duplication within a top-level templating operation.
    """
    # deprecated: description='enable top-level facts deprecation' core_version='2.20'
    # return _DEPRECATE_TOP_LEVEL_FACT_TAG.tag(value)
    return value


def preprocess_vars(a):
    """
    Ensures that vars contained in the parameter passed in are
    returned as a list of dictionaries, to ensure for instance
    that vars loaded from a file conform to an expected state.
    """

    # FIXME: this does not properly handle omit, undefined, or dynamic structure from templated `vars` ; templating should be done earlier
    if a is None:
        return None
    elif not isinstance(a, list):
        data = [a]
    else:
        data = a

    for item in data:
        if not isinstance(item, MutableMapping):
            raise AnsibleParserError(
                message="Invalid variable file contents.",
                obj=item,
                help_text="Variable files must contain either a dictionary of variables, or a list of dictionaries.",
            )

    return data


class VariableManager:

    _ALLOWED = frozenset(['plugins_by_group', 'groups_plugins_play', 'groups_plugins_inventory', 'groups_inventory',
                          'all_plugins_play', 'all_plugins_inventory', 'all_inventory'])

    _PLAY_HOSTS_DEPRECATED_TAG = _tags.Deprecated(
        msg='The `play_hosts` magic variable is deprecated.',
        version='2.23',
        deprecator=_deprecator.ANSIBLE_CORE_DEPRECATOR,
        help_text='Use `ansible_play_batch` instead.',
    )

    def __init__(self, loader: DataLoader | None = None, inventory: InventoryManager | None = None, version_info: dict[str, str] | None = None) -> None:
        self._nonpersistent_fact_cache: defaultdict[str, dict] = defaultdict(dict)
        self._vars_cache: defaultdict[str, dict] = defaultdict(dict)
        self._inventory = inventory
        self._loader = loader
        self._hostvars: HostVars | None = None

        self._options_vars = load_options_vars(version_info)

        # If the basedir is specified as the empty string then it results in cwd being used.
        # This is not a safe location to load vars from.
        basedir = self._options_vars.get('basedir', False)
        self.safe_basedir = bool(basedir is False or basedir)

        # load extra vars
        self._extra_vars = load_extra_vars(loader=self._loader)

        # load fact cache
        try:
            self._fact_cache = cache_loader.get(C.CACHE_PLUGIN)
        except Exception as ex:
            # bad cache plugin is not fatal error
            # fallback to builtin memory cache plugin
            display.error_as_warning(None, ex)
            self._fact_cache = cache_loader.get('ansible.builtin.memory')  # use FQCN to ensure the builtin version is used

    @property
    def extra_vars(self):
        return self._extra_vars

    def set_inventory(self, inventory):
        self._inventory = inventory

    def get_vars(
        self,
        play: Play | None = None,
        host: Host | None = None,
        task: Task | None = None,
        include_hostvars: bool = True,
        use_cache: bool = True,
        _hosts: list[str] | None = None,
        _hosts_all: list[str] | None = None,
        stage: str = 'task',
    ) -> dict[str, t.Any]:
        """
        Returns the variables, with optional "context" given via the parameters
        for the play, host, and task (which could possibly result in different
        sets of variables being returned due to the additional context).

        The order of precedence is:
        - play->roles->get_default_vars (if there is a play context)
        - group_vars_files[host] (if there is a host context)
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
        """

        display.debug("in VariableManager get_vars()")

        all_vars: dict[str, t.Any] = dict()
        magic_variables = self._get_magic_variables(
            play=play,
            host=host,
            task=task,
            include_hostvars=include_hostvars,
            _hosts=_hosts,
            _hosts_all=_hosts_all,
        )

        def _combine_and_track(data, new_data, source):
            # FIXME: this no longer does any tracking, only a slight optimization for empty new_data
            if new_data == {}:
                return data

            return combine_vars(data, new_data)

        # default for all cases
        basedirs = []
        if self.safe_basedir:  # avoid adhoc/console loading cwd
            basedirs = [self._loader.get_basedir()]

        if play:
            # get role defaults (lowest precedence)
            for role in play.roles:
                if role.public:
                    all_vars = _combine_and_track(all_vars, role.get_default_vars(), "role '%s' defaults" % role.name)

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
            # TODO: investigate why we need play or include_role check?
            if task._role is not None and (play or task.action in C._ACTION_INCLUDE_ROLE):
                all_vars = _combine_and_track(all_vars, task._role.get_default_vars(dep_chain=task.get_dep_chain()), "role '%s' defaults" % task._role.name)

        if host:
            # THE 'all' group and the rest of groups for a host, used below
            all_group = self._inventory.groups.get('all')
            host_groups = sort_groups([g for g in host.get_groups() if g.name != 'all'])

            # internal functions that actually do the work
            def _plugins_inventory(entities):
                """ merges all entities by inventory source """
                return get_vars_from_inventory_sources(self._loader, self._inventory._sources, entities, stage)

            def _plugins_play(entities):
                """ merges all entities adjacent to play """
                data = {}
                for path in basedirs:
                    data = _combine_and_track(data, get_vars_from_path(self._loader, path, entities, stage), "path '%s'" % path)
                return data

            # configurable functions that are sortable via config, remember to add to _ALLOWED if expanding this list
            def all_inventory():
                return all_group.get_vars()

            def all_plugins_inventory():
                return _plugins_inventory([all_group])

            def all_plugins_play():
                return _plugins_play([all_group])

            def groups_inventory():
                """ gets group vars from inventory """
                return get_group_vars(host_groups)

            def groups_plugins_inventory():
                """ gets plugin sources from inventory for groups """
                return _plugins_inventory(host_groups)

            def groups_plugins_play():
                """ gets plugin sources from play for groups """
                return _plugins_play(host_groups)

            def plugins_by_groups():
                """
                    merges all plugin sources by group,
                    This should be used instead, NOT in combination with the other groups_plugins* functions
                """
                data = {}
                for group in host_groups:
                    data[group] = _combine_and_track(data[group], _plugins_inventory(group), "inventory group_vars for '%s'" % group)
                    data[group] = _combine_and_track(data[group], _plugins_play(group), "playbook group_vars for '%s'" % group)
                return data

            # Merge groups as per precedence config
            # only allow to call the functions we want exposed
            for entry in C.VARIABLE_PRECEDENCE:
                if entry in self._ALLOWED:
                    display.debug('Calling %s to load vars for %s' % (entry, host.name))
                    all_vars = _combine_and_track(all_vars, locals()[entry](), "group vars, precedence entry '%s'" % entry)
                else:
                    display.warning('Ignoring unknown variable precedence entry: %s' % (entry))

            # host vars, from inventory, inventory adjacent and play adjacent via plugins
            all_vars = _combine_and_track(all_vars, host.get_vars(), "host vars for '%s'" % host)
            all_vars = _combine_and_track(all_vars, _plugins_inventory([host]), "inventory host_vars for '%s'" % host)
            all_vars = _combine_and_track(all_vars, _plugins_play([host]), "playbook host_vars for '%s'" % host)

            # finally, the facts caches for this host, if it exists
            # TODO: cleaning of facts should eventually become part of taskresults instead of vars
            try:
                try:
                    facts = self._fact_cache.get(host.name)
                except KeyError:
                    facts = {}

                all_vars |= namespace_facts(facts)

                # push facts to main namespace
                if C.INJECT_FACTS_AS_VARS:
                    deprecated_facts_vars = {k: _deprecate_top_level_fact(v) for k, v in clean_facts(facts).items()}
                    all_vars = _combine_and_track(all_vars, deprecated_facts_vars, "facts")
                else:
                    # always 'promote' ansible_local
                    all_vars = _combine_and_track(all_vars, {'ansible_local': facts.get('ansible_local', {})}, "facts")
            except KeyError:
                pass

        if play:
            all_vars = _combine_and_track(all_vars, play.get_vars(), "play vars")

            vars_files = play.get_vars_files()

            for vars_file_item in vars_files:
                # create a set of temporary vars here, which incorporate the extra
                # and magic vars so we can properly template the vars_files entries
                # NOTE: this makes them depend on host vars/facts so things like
                #       ansible_facts['os_distribution'] can be used, ala include_vars.
                #       Consider DEPRECATING this in the future, since we have include_vars ...
                temp_vars = combine_vars(all_vars, self._extra_vars)
                temp_vars = combine_vars(temp_vars, magic_variables)
                templar = TemplateEngine(loader=self._loader, variables=temp_vars)

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
                        if not (isinstance(vars_file, str)):
                            raise AnsibleParserError(
                                message=f"Invalid `vars_files` value of type {native_type_name(vars_file)!r}.",
                                obj=vars_file,
                                help_text="A `vars_files` value should either be a string or list of strings.",
                            )
                        try:
                            play_search_stack = play.get_search_path()
                            found_file = self._loader.path_dwim_relative_stack(play_search_stack, 'vars', vars_file)
                            data = preprocess_vars(self._loader.load_from_file(found_file, unsafe=True, cache='vaulted', trusted_as_template=True))
                            if data is not None:
                                for item in data:
                                    all_vars = _combine_and_track(all_vars, item, "play vars_files from '%s'" % vars_file)
                            display.vvv(f"Read `vars_file` {found_file!r}.")
                            break
                        except AnsibleFileNotFound:
                            # we continue on loader failures
                            continue
                        except AnsibleParserError:
                            raise
                        except AnsibleUndefinedVariable:
                            raise
                        except Exception as ex:
                            raise AnsibleParserError(f"Error reading `vars_files` file {vars_file!r}.", obj=vars_file) from ex

                except AnsibleUndefinedVariable as ex:
                    if host is not None:
                        try:
                            facts = self._fact_cache.get(host.name)
                        except KeyError:
                            pass
                        else:
                            if facts.get('module_setup') and task is not None:
                                raise AnsibleUndefinedVariable("an undefined variable was found when attempting to template the vars_files item '%s'"
                                                               % vars_file_item, obj=vars_file_item) from ex

                    display.warning("skipping vars_file item due to an undefined variable", obj=vars_file_item)
                    continue

            # We now merge in all exported vars from all roles in the play (very high precedence)
            for role in play.roles:
                if role.public:
                    all_vars = _combine_and_track(all_vars, role.get_vars(include_params=False, only_exports=True), "role '%s' exported vars" % role.name)

        # next, we merge in the vars from the role, which will specifically
        # follow the role dependency chain, and then we merge in the tasks
        # vars (which will look at parent blocks/task includes)
        if task:
            if task._role:
                all_vars = _combine_and_track(all_vars, task._role.get_vars(task.get_dep_chain(), include_params=False, only_exports=False),
                                              "role '%s' all vars" % task._role.name)
            all_vars = _combine_and_track(all_vars, task.get_vars(), "task vars")

        # next, we merge in the vars cache (include vars) and nonpersistent
        # facts cache (set_fact/register), in that order
        if host:
            # include_vars non-persistent cache
            all_vars = _combine_and_track(all_vars, self._vars_cache.get(host.get_name(), dict()), "include_vars")
            # fact non-persistent cache
            all_vars = _combine_and_track(all_vars, self._nonpersistent_fact_cache.get(host.name, dict()), "set_fact")

        # next, we merge in role params and task include params
        if task:
            # special case for include tasks, where the include params
            # may be specified in the vars field for the task, which should
            # have higher precedence than the vars/np facts above
            if task._role:
                all_vars = _combine_and_track(all_vars, task._role.get_role_params(task.get_dep_chain()), "role params")
            all_vars = _combine_and_track(all_vars, task.get_include_params(), "include params")

        # extra vars
        all_vars = _combine_and_track(all_vars, self._extra_vars, "extra vars")

        # before we add 'reserved vars', check we didn't add any reserved vars
        warn_if_reserved(all_vars)

        # magic variables
        all_vars = _combine_and_track(all_vars, magic_variables, "magic vars")

        # special case for the 'environment' magic variable, as someone
        # may have set it as a variable and we don't want to stomp on it
        if task:
            all_vars['environment'] = task.environment

        # 'vars' magic var
        if task or play:
            # has to be copy, otherwise recursive ref
            all_vars['vars'] = all_vars.copy()

        display.debug("done with get_vars()")
        return all_vars

    def _facts_gathered_for_host(self, hostname) -> bool:
        try:
            facts = self._fact_cache.get(hostname)
        except KeyError:
            facts = {}

        return bool(facts.get('_ansible_facts_gathered', False))

    def _get_magic_variables(self, play, host, task, include_hostvars, _hosts=None, _hosts_all=None):
        """
        Returns a dictionary of so-called "magic" variables in Ansible,
        which are special variables we set internally for use.
        """

        variables = {}
        variables['playbook_dir'] = os.path.abspath(self._loader.get_basedir())
        variables['ansible_playbook_python'] = sys.executable
        variables['ansible_config_file'] = C.CONFIG_FILE

        if play:
            # using role_cache as play.roles only has 'public' roles for vars exporting
            dependency_role_names = list({d.get_name() for r in play.roles for d in r.get_all_dependencies()})
            play_role_names = [r.get_name() for r in play.roles]

            # ansible_role_names includes all role names, dependent or directly referenced by the play
            variables['ansible_role_names'] = list(set(dependency_role_names + play_role_names))
            # ansible_play_role_names includes the names of all roles directly referenced by this play
            # roles that are implicitly referenced via dependencies are not listed.
            variables['ansible_play_role_names'] = play_role_names
            # ansible_dependent_role_names includes the names of all roles that are referenced via dependencies
            # dependencies that are also explicitly named as roles are included in this list
            variables['ansible_dependent_role_names'] = dependency_role_names

            # TODO: data tagging!!! DEPRECATED: role_names should be deprecated in favor of ansible_ prefixed ones
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
                # add the list of hosts in the play, as adjusted for limit/filters
                if not _hosts_all:
                    if not play.finalized and TemplateEngine().is_template(play.hosts):
                        pattern = 'all'
                    else:
                        pattern = play.hosts or 'all'

                    _hosts_all = [h.name for h in self._inventory.get_hosts(pattern=pattern, ignore_restrictions=True)]
                if not _hosts:
                    _hosts = [h.name for h in self._inventory.get_hosts()]

                variables['ansible_play_hosts_all'] = _hosts_all[:]
                variables['ansible_play_hosts'] = [x for x in variables['ansible_play_hosts_all'] if x not in play._removed_hosts]
                variables['ansible_play_batch'] = [x for x in _hosts if x not in play._removed_hosts]

                # use a static tag instead of `deprecate_value` to avoid stackwalk in a hot code path
                variables['play_hosts'] = self._PLAY_HOSTS_DEPRECATED_TAG.tag(variables['ansible_play_batch'])

        # Set options vars
        for option, option_value in self._options_vars.items():
            variables[option] = option_value

        if self._hostvars is not None and include_hostvars:
            variables['hostvars'] = self._hostvars

        return variables

    def get_delegated_vars_and_hostname(self, templar, task, variables):
        """Get the delegated_vars for an individual task invocation, which may be in the context
        of an individual loop iteration.

        Not used directly be VariableManager, but used primarily within TaskExecutor
        """
        delegated_vars = {}
        delegated_host_name = ...  # sentinel value distinct from empty/None, which are errors

        if task.delegate_to:
            try:
                delegated_host_name = templar.template(task.delegate_to)
            except AnsibleValueOmittedError:
                pass

        # bypass for unspecified value/omit
        if delegated_host_name is ...:
            return delegated_vars, None

        if not delegated_host_name:
            raise AnsibleError('Empty hostname produced from delegate_to: "%s"' % task.delegate_to)

        delegated_host = self._inventory.get_host(delegated_host_name)
        if delegated_host is None:
            for h in self._inventory.get_hosts(ignore_limits=True, ignore_restrictions=True):
                # check if the address matches, or if both the delegated_to host
                # and the current host are in the list of localhost aliases
                if h.address == delegated_host_name:
                    delegated_host = h
                    break
            else:
                delegated_host = Host(name=delegated_host_name)

        delegated_vars['ansible_delegated_vars'] = {
            delegated_host_name: self.get_vars(
                play=task.get_play(),
                host=delegated_host,
                task=task,
                include_hostvars=True,
            )
        }
        delegated_vars['ansible_delegated_vars'][delegated_host_name]['inventory_hostname'] = variables.get('inventory_hostname')

        return delegated_vars, delegated_host_name

    def clear_facts(self, hostname):
        """
        Clears the facts for a host
        """
        try:
            self._fact_cache.delete(hostname)
        except KeyError:
            pass

    def set_host_facts(self, host, facts):
        """
        Sets or updates the given facts for a host in the fact cache.
        """

        if not isinstance(facts, Mapping):
            raise AnsibleAssertionError("the type of 'facts' to set for host_facts should be a Mapping but is a %s" % type(facts))

        warn_if_reserved(facts)

        try:
            host_cache = self._fact_cache.get(host)
        except KeyError:
            # We get to set this as new
            host_cache = facts
        else:
            if not isinstance(host_cache, MutableMapping):
                raise TypeError('The object retrieved for {0} must be a MutableMapping but was'
                                ' a {1}'.format(host, type(host_cache)))
            # Update the existing facts
            host_cache |= facts

        # Save the facts back to the backing store
        self._fact_cache.set(host, host_cache)

    def set_nonpersistent_facts(self, host, facts):
        """
        Sets or updates the given facts for a host in the fact cache.
        """

        if not isinstance(facts, Mapping):
            raise AnsibleAssertionError("the type of 'facts' to set for nonpersistent_facts should be a Mapping but is a %s" % type(facts))

        warn_if_reserved(facts)

        try:
            self._nonpersistent_fact_cache[host] |= facts
        except KeyError:
            self._nonpersistent_fact_cache[host] = facts

    def set_host_variable(self, host, varname, value):
        """
        Sets a value in the vars_cache for a host.
        """

        warn_if_reserved([varname])

        if host not in self._vars_cache:
            self._vars_cache[host] = dict()

        if varname in self._vars_cache[host] and isinstance(self._vars_cache[host][varname], MutableMapping) and isinstance(value, MutableMapping):
            self._vars_cache[host] = combine_vars(self._vars_cache[host], {varname: value})
        else:
            self._vars_cache[host][varname] = value
