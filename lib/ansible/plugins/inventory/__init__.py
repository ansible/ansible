# (c) 2017,  Red Hat, inc
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
# along with Ansible.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import functools
import hashlib
import os
import string
import typing as t

from collections.abc import Mapping

from ansible import template as _template
from ansible.errors import AnsibleError, AnsibleParserError, AnsibleValueOmittedError
from ansible.inventory.group import to_safe_group_name as original_safe
from ansible.module_utils._internal import _plugin_info
from ansible.parsing.utils.addresses import parse_address
from ansible.parsing.dataloader import DataLoader
from ansible.plugins import AnsiblePlugin, _ConfigurablePlugin
from ansible.plugins.cache import CachePluginAdjudicator
from ansible.module_utils.common.text.converters import to_bytes, to_native
from ansible.utils.display import Display
from ansible.utils.vars import combine_vars, load_extra_vars

if t.TYPE_CHECKING:
    from ansible.inventory.data import InventoryData

display = Display()


# Helper methods
def to_safe_group_name(name):
    # placeholder for backwards compat
    return original_safe(name, force=True, silent=True)


def detect_range(line=None):
    """
    A helper function that checks a given host line to see if it contains
    a range pattern described in the docstring above.

    Returns True if the given line contains a pattern, else False.
    """
    return '[' in line


def expand_hostname_range(line=None):
    """
    A helper function that expands a given line that contains a pattern
    specified in top docstring, and returns a list that consists of the
    expanded version.

    The '[' and ']' characters are used to maintain the pseudo-code
    appearance. They are replaced in this function with '|' to ease
    string splitting.

    References: https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html#hosts-and-groups
    """
    all_hosts = []
    if line:
        # A hostname such as db[1:6]-node is considered to consists
        # three parts:
        # head: 'db'
        # nrange: [1:6]; range() is a built-in. Can't use the name
        # tail: '-node'

        # Add support for multiple ranges in a host so:
        # db[01:10:3]node-[01:10]
        # - to do this we split off at the first [...] set, getting the list
        #   of hosts and then repeat until none left.
        # - also add an optional third parameter which contains the step. (Default: 1)
        #   so range can be [01:10:2] -> 01 03 05 07 09

        (head, nrange, tail) = line.replace('[', '|', 1).replace(']', '|', 1).split('|')
        bounds = nrange.split(":")
        if len(bounds) != 2 and len(bounds) != 3:
            raise AnsibleError("host range must be begin:end or begin:end:step")
        beg = bounds[0]
        end = bounds[1]
        if len(bounds) == 2:
            step = 1
        else:
            step = bounds[2]
        if not beg:
            beg = "0"
        if not end:
            raise AnsibleError("host range must specify end value")
        if beg[0] == '0' and len(beg) > 1:
            rlen = len(beg)  # range length formatting hint
            if rlen != len(end):
                raise AnsibleError("host range must specify equal-length begin and end formats")

            def fill(x):
                return str(x).zfill(rlen)  # range sequence

        else:
            fill = str

        try:
            i_beg = string.ascii_letters.index(beg)
            i_end = string.ascii_letters.index(end)
            if i_beg > i_end:
                raise AnsibleError("host range must have begin <= end")
            seq = list(string.ascii_letters[i_beg:i_end + 1:int(step)])
        except ValueError:  # not an alpha range
            seq = range(int(beg), int(end) + 1, int(step))

        for rseq in seq:
            hname = ''.join((head, fill(rseq), tail))

            if detect_range(hname):
                all_hosts.extend(expand_hostname_range(hname))
            else:
                all_hosts.append(hname)

        return all_hosts


def get_cache_plugin(plugin_name, **kwargs):
    if not plugin_name:
        raise AnsibleError("A cache plugin must be configured to use inventory caching.")

    try:
        cache = CachePluginAdjudicator(plugin_name, **kwargs)
    except AnsibleError as e:
        if 'fact_caching_connection' in to_native(e):
            raise AnsibleError("error, '%s' inventory cache plugin requires the one of the following to be set "
                               "to a writeable directory path:\nansible.cfg:\n[default]: fact_caching_connection,\n"
                               "[inventory]: cache_connection;\nEnvironment:\nANSIBLE_INVENTORY_CACHE_CONNECTION,\n"
                               "ANSIBLE_CACHE_PLUGIN_CONNECTION." % plugin_name)
        else:
            raise

    if cache._plugin.ansible_name != 'ansible.builtin.memory' and kwargs and not getattr(cache._plugin, '_options', None):
        raise AnsibleError('Unable to use cache plugin {0} for inventory. Cache options were provided but may not reconcile '
                           'correctly unless set via set_options. Refer to the porting guide if the plugin derives user settings '
                           'from ansible.constants.'.format(plugin_name))
    return cache


class _BaseInventoryPlugin(AnsiblePlugin):
    """
    Internal base implementation for inventory plugins.

    Do not inherit from this directly, use one of its public subclasses instead.
    Used to introduce an extra layer in the class hierarchy to allow Constructed to subclass this while remaining a mixin for existing inventory plugins.
    """

    TYPE = 'generator'

    # 3rd party plugins redefine this to
    # use custom group name sanitization
    # since constructed features enforce
    # it by default.
    _sanitize_group_name = staticmethod(to_safe_group_name)

    def __init__(self) -> None:

        super().__init__()

        self._options = {}
        self.display = display

        # These attributes are set by the parse() method on this (base) class.
        self.loader: DataLoader | None = None
        self.inventory: InventoryData | None = None
        self._vars: dict[str, t.Any] | None = None

    trusted_by_default: bool = False
    """Inventory plugins that only source templates from trusted sources can set this True to have trust automatically applied to all templates."""

    @functools.cached_property
    def templar(self) -> _template.Templar:
        return _template.Templar(loader=self.loader)

    def parse(self, inventory: InventoryData, loader: DataLoader, path: str, cache: bool = True) -> None:
        """ Populates inventory from the given data. Raises an error on any parse failure
            :arg inventory: a copy of the previously accumulated inventory data,
                 to be updated with any new data this plugin provides.
                 The inventory can be empty if no other source/plugin ran successfully.
            :arg loader: a reference to the DataLoader, which can read in YAML and JSON files,
                 it also has Vault support to automatically decrypt files.
            :arg path: the string that represents the 'inventory source',
                 normally a path to a configuration file for this inventory,
                 but it can also be a raw string for this plugin to consume
            :arg cache: a boolean that indicates if the plugin should use the cache or not
                 you can ignore if this plugin does not implement caching.
        """
        self.loader = loader
        self.inventory = inventory
        self._vars = load_extra_vars(loader)

    def verify_file(self, path):
        """ Verify if file is usable by this plugin, base does minimal accessibility check
            :arg path: a string that was passed as an inventory source,
                 it normally is a path to a config file, but this is not a requirement,
                 it can also be parsed itself as the inventory data to process.
                 So only call this base class if you expect it to be a file.
        """

        valid = False
        b_path = to_bytes(path, errors='surrogate_or_strict')
        if (os.path.exists(b_path) and os.access(b_path, os.R_OK)):
            valid = True
        else:
            self.display.vvv('Skipping due to inventory source not existing or not being readable by the current user')
        return valid

    def _populate_host_vars(self, hosts, variables, group=None, port=None):
        if not isinstance(variables, Mapping):
            raise AnsibleParserError("Invalid data from file, expected dictionary and got:\n\n%s" % to_native(variables))

        for host in hosts:
            self.inventory.add_host(host, group=group, port=port)
            for k in variables:
                self.inventory.set_variable(host, k, variables[k])

    def _read_config_data(self, path):
        """ validate config and set options as appropriate
            :arg path: path to common yaml format config file for this plugin
        """

        try:
            # avoid loader cache so meta: refresh_inventory can pick up config changes
            # if we read more than once, fs cache should be good enough
            config = self.loader.load_from_file(path, cache='none', trusted_as_template=True)
        except Exception as e:
            raise AnsibleParserError(to_native(e))

        # a plugin can be loaded via many different names with redirection- if so, we want to accept any of those names
        valid_names = getattr(self, '_redirected_names') or [self.NAME]

        if not config:
            # no data
            raise AnsibleParserError("%s is empty" % (to_native(path)))
        elif config.get('plugin') not in valid_names:
            # this is not my config file
            raise AnsibleParserError("Incorrect plugin name in file: %s" % config.get('plugin', 'none found'))
        elif not isinstance(config, Mapping):
            # configs are dictionaries
            raise AnsibleParserError('inventory source has invalid structure, it should be a dictionary, got: %s' % type(config))

        self.set_options(direct=config, var_options=self._vars)
        if 'cache' in self._options and self.get_option('cache'):
            cache_option_keys = [('_uri', 'cache_connection'), ('_timeout', 'cache_timeout'), ('_prefix', 'cache_prefix')]
            cache_options = dict((opt[0], self.get_option(opt[1])) for opt in cache_option_keys if self.get_option(opt[1]) is not None)
            self._cache = get_cache_plugin(self.get_option('cache_plugin'), **cache_options)

        return config

    def _consume_options(self, data):
        """ update existing options from alternate configuration sources not normally used by Ansible.
            Many API libraries already have existing configuration sources, this allows plugin author to leverage them.
            :arg data: key/value pairs that correspond to configuration options for this plugin
        """

        for k in self._options:
            if k in data:
                self._options[k] = data.pop(k)

    def _expand_hostpattern(self, hostpattern):
        """
        Takes a single host pattern and returns a list of hostnames and an
        optional port number that applies to all of them.
        """
        # Can the given hostpattern be parsed as a host with an optional port
        # specification?

        try:
            (pattern, port) = parse_address(hostpattern, allow_ranges=True)
        except Exception:
            # not a recognizable host pattern
            pattern = hostpattern
            port = None

        # Once we have separated the pattern, we expand it into list of one or
        # more hostnames, depending on whether it contains any [x:y] ranges.

        if detect_range(pattern):
            hostnames = expand_hostname_range(pattern)
        else:
            hostnames = [pattern]

        return (hostnames, port)


class BaseInventoryPlugin(_BaseInventoryPlugin):
    """ Parses an Inventory Source """


class BaseFileInventoryPlugin(_BaseInventoryPlugin):
    """ Parses a File based Inventory Source"""

    TYPE = 'storage'

    def __init__(self):

        super(BaseFileInventoryPlugin, self).__init__()


class Cacheable(_plugin_info.HasPluginInfo, _ConfigurablePlugin):
    """Mixin for inventory plugins which support caching."""

    _cache: CachePluginAdjudicator

    @property
    def cache(self) -> CachePluginAdjudicator:
        return self._cache

    def load_cache_plugin(self) -> None:
        plugin_name = self.get_option('cache_plugin')
        cache_option_keys = [('_uri', 'cache_connection'), ('_timeout', 'cache_timeout'), ('_prefix', 'cache_prefix')]
        cache_options = dict((opt[0], self.get_option(opt[1])) for opt in cache_option_keys if self.get_option(opt[1]) is not None)
        self._cache = get_cache_plugin(plugin_name, **cache_options)

    def get_cache_key(self, path: str) -> str:
        return f'{self.ansible_name}_{self._get_cache_prefix(path)}'

    def _get_cache_prefix(self, path: str) -> str:
        """Return a predictable unique key based on the given path."""
        return 'k' + hashlib.sha256(f'{self.ansible_name}{path}'.encode(), usedforsecurity=False).hexdigest()[:6]

    def clear_cache(self) -> None:
        self._cache.clear()

    def update_cache_if_changed(self) -> None:
        self._cache.update_cache_if_changed()

    def set_cache_plugin(self) -> None:
        self._cache.set_cache()


class Constructable(_BaseInventoryPlugin):
    def _compose(self, template, variables, disable_lookups=...):
        """ helper method for plugins to compose variables for Ansible based on jinja2 expression and inventory vars"""
        if disable_lookups is not ...:
            self.display.deprecated("The disable_lookups arg has no effect.", version="2.23")

        try:
            use_extra = self.get_option('use_extra_vars')
        except Exception:
            use_extra = False

        if use_extra:
            self.templar.available_variables = combine_vars(variables, self._vars)
        else:
            self.templar.available_variables = variables

        return self.templar.evaluate_expression(template)

    def _set_composite_vars(self, compose, variables, host, strict=False):
        """ loops over compose entries to create vars for hosts """
        if compose and isinstance(compose, dict):
            for varname in compose:
                try:
                    composite = self._compose(compose[varname], variables)
                except Exception as e:
                    if strict:
                        raise AnsibleError("Could not set %s for host %s: %s" % (varname, host, to_native(e)))
                    continue
                self.inventory.set_variable(host, varname, composite)

    def _add_host_to_composed_groups(self, groups, variables, host, strict=False, fetch_hostvars=True):
        """ helper to create complex groups for plugins based on jinja2 conditionals, hosts that meet the conditional are added to group"""
        # process each 'group entry'
        if groups and isinstance(groups, dict):
            if fetch_hostvars:
                variables = combine_vars(variables, self.inventory.get_host(host).get_vars())
            self.templar.available_variables = variables
            for group_name in groups:
                conditional = groups[group_name]
                group_name = self._sanitize_group_name(group_name)
                try:
                    result = self.templar.evaluate_conditional(conditional)
                except Exception as e:
                    if strict:
                        raise AnsibleParserError("Could not add host %s to group %s: %s" % (host, group_name, to_native(e)))
                    continue

                if result:
                    # ensure group exists, use sanitized name
                    group_name = self.inventory.add_group(group_name)
                    # add host to group
                    self.inventory.add_child(group_name, host)

    def _add_host_to_keyed_groups(self, keys, variables, host, strict=False, fetch_hostvars=True):
        """ helper to create groups for plugins based on variable values and add the corresponding hosts to it"""
        should_default_value = (None, '')

        if keys and isinstance(keys, list):
            for keyed in keys:
                if keyed and isinstance(keyed, dict):

                    if fetch_hostvars:
                        variables = combine_vars(variables, self.inventory.get_host(host).get_vars())
                    try:
                        key = self._compose(keyed.get('key'), variables)
                    except Exception as e:
                        if strict:
                            raise AnsibleParserError("Could not generate group for host %s from %s entry: %s" % (host, keyed.get('key'), to_native(e)))
                        continue
                    default_value_name = keyed.get('default_value', None)
                    trailing_separator = keyed.get('trailing_separator')
                    if trailing_separator is not None and default_value_name is not None:
                        raise AnsibleParserError("parameters are mutually exclusive for keyed groups: default_value|trailing_separator")

                    use_default = key in should_default_value and default_value_name is not None
                    if key or use_default:
                        prefix = keyed.get('prefix', '')
                        sep = keyed.get('separator', '_')
                        raw_parent_name = keyed.get('parent_group', None)

                        try:
                            raw_parent_name = self.templar.template(raw_parent_name)
                        except AnsibleValueOmittedError:
                            raw_parent_name = None
                        except Exception as ex:
                            if strict:
                                raise AnsibleParserError(f'Could not generate parent group {raw_parent_name!r} for group {key!r}: {ex}') from ex

                            continue

                        new_raw_group_names = []
                        if use_default:
                            new_raw_group_names.append(default_value_name)
                        elif isinstance(key, str):
                            new_raw_group_names.append(key)
                        elif isinstance(key, list):
                            for name in key:
                                # if list item is empty, 'default_value' will be used as group name
                                if name in should_default_value and default_value_name is not None:
                                    new_raw_group_names.append(default_value_name)
                                else:
                                    new_raw_group_names.append(name)
                        elif isinstance(key, Mapping):
                            for (gname, gval) in key.items():
                                bare_name = '%s%s%s' % (gname, sep, gval)
                                if gval in should_default_value:
                                    # key's value is empty
                                    if default_value_name is not None:
                                        bare_name = '%s%s%s' % (gname, sep, default_value_name)
                                    elif trailing_separator is False:
                                        bare_name = gname
                                new_raw_group_names.append(bare_name)
                        else:
                            raise AnsibleParserError("Invalid group name format, expected a string or a list of them or dictionary, got: %s" % type(key))

                        for bare_name in new_raw_group_names:
                            if prefix == '' and self.get_option('leading_separator') is False:
                                sep = ''
                            gname = self._sanitize_group_name('%s%s%s' % (prefix, sep, bare_name))
                            result_gname = self.inventory.add_group(gname)
                            self.inventory.add_host(host, result_gname)

                            if raw_parent_name:
                                parent_name = self._sanitize_group_name(raw_parent_name)
                                self.inventory.add_group(parent_name)
                                self.inventory.add_child(parent_name, result_gname)

                    else:
                        # exclude case of empty list and dictionary, because these are valid constructions
                        # simply no groups need to be constructed, but are still falsy
                        if strict and key not in ([], {}):
                            raise AnsibleParserError("No key or key resulted empty for %s in host %s, invalid entry" % (keyed.get('key'), host))
                else:
                    raise AnsibleParserError("Invalid keyed group entry, it must be a dictionary: %s " % keyed)
