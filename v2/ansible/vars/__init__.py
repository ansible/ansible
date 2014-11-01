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

from ansible.parsing.yaml import DataLoader
from ansible.plugins.cache import FactCache

class VariableManager:

    def __init__(self, inventory_path=None, loader=None):

        self._fact_cache       = FactCache()
        self._vars_cache       = defaultdict(dict)
        self._extra_vars       = defaultdict(dict)
        self._host_vars_files  = defaultdict(dict)
        self._group_vars_files = defaultdict(dict)

        if not loader:
            self._loader = DataLoader()
        else:
            self._loader = loader

    @property
    def extra_vars(self):
        ''' ensures a clean copy of the extra_vars are made '''
        return self._extra_vars.copy()

    def set_extra_vars(self, value):
        ''' ensures a clean copy of the extra_vars are used to set the value '''
        assert isinstance(value, dict)
        self._extra_vars = value.copy()

    def _merge_dicts(self, a, b):
        '''
        Recursively merges dict b into a, so that keys
        from b take precedence over keys from a.
        '''

        result = dict()

        # FIXME: do we need this from utils, or should it just
        #        be merged into this definition?
        #_validate_both_dicts(a, b)

        for dicts in a, b:
            # next, iterate over b keys and values
            for k, v in dicts.iteritems():
                # if there's already such key in a
                # and that key contains dict
                if k in result and isinstance(result[k], dict):
                    # merge those dicts recursively
                    result[k] = self._merge_dicts(a[k], v)
                else:
                    # otherwise, just copy a value from b to a
                    result[k] = v

        return result

    def get_vars(self, play=None, host=None, task=None):
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
        - vars_cache[host] (if there is a host context)
        - play vars (if there is a play context)
        - play vars_files (if there's no host context, ignore
          file names that cannot be templated)
        - task->get_vars (if there is a task context)
        - extra vars
        '''

        vars = defaultdict(dict)

        if play:
            # first we compile any vars specified in defaults/main.yml
            # for all roles within the specified play
            for role in play.get_roles():
                vars = self._merge_dicts(vars, role.get_default_vars())

        if host:
            # next, if a host is specified, we load any vars from group_vars
            # files and then any vars from host_vars files which may apply to
            # this host or the groups it belongs to
            for group in host.get_groups():
                if group in self._group_vars_files:
                    vars = self._merge_dicts(vars, self._group_vars_files[group])

            host_name = host.get_name()
            if host_name in self._host_vars_files:
                vars = self._merge_dicts(vars, self._host_vars_files[host_name])

            # then we merge in vars specified for this host
            vars = self._merge_dicts(vars, host.get_vars())

            # next comes the facts cache and the vars cache, respectively
            vars = self._merge_dicts(vars, self._fact_cache.get(host.get_name(), dict()))
            vars = self._merge_dicts(vars, self._vars_cache.get(host.get_name(), dict()))

        if play:
            vars = self._merge_dicts(vars, play.get_vars())
            for vars_file in play.get_vars_files():
                # Try templating the vars_file. If an unknown var error is raised,
                # ignore it - unless a host is specified
                # TODO ...

                data = self._loader.load_from_file(vars_file)
                vars = self._merge_dicts(vars, data)

        if task:
            vars = self._merge_dicts(vars, task.get_vars())

        vars = self._merge_dicts(vars, self._extra_vars)

        return vars

    def _get_inventory_basename(self, path):
        '''
        Returns the bsaename minus the extension of the given path, so the
        bare filename can be matched against host/group names later
        '''

        (name, ext) = os.path.splitext(os.path.basename(path))
        return name

    def _load_inventory_file(self, path):
        '''
        helper function, which loads the file and gets the
        basename of the file without the extension
        '''

        data = self._loader.load_from_file(path)
        name = self._get_inventory_basename(path)
        return (name, data)

    def add_host_vars_file(self, path):
        '''
        Loads and caches a host_vars file in the _host_vars_files dict,
        where the key to that dictionary is the basename of the file, minus
        the extension, for matching against a given inventory host name
        '''

        (name, data) = self._load_inventory_file(path)
        self._host_vars_files[name] = data

    def add_group_vars_file(self, path):
        '''
        Loads and caches a host_vars file in the _host_vars_files dict,
        where the key to that dictionary is the basename of the file, minus
        the extension, for matching against a given inventory host name
        '''

        (name, data) = self._load_inventory_file(path)
        self._group_vars_files[name] = data

