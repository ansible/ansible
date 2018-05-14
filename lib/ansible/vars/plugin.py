# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.inventory.host import Host
from ansible.plugins.loader import vars_loader
from ansible.utils.vars import combine_vars

__slots__ = ['get_plugin_vars']


def _get_vars_from_plugin(plugin, loader, path, entities):

    data = {}
    for entity in entities:
        try:
            data = plugin.get_vars(loader, path, entity)
        except AttributeError:
            try:
                if isinstance(entity, Host):
                    data = combine_vars(data, plugin.get_host_vars(entity.name))
                else:
                    data = combine_vars(data, plugin.get_group_vars(entity.name))
            except AttributeError:
                if hasattr(plugin, 'run'):
                    raise AnsibleError("Cannot use v1 type vars plugin %s from %s" % (plugin._load_name, plugin._original_path))
                else:
                    raise AnsibleError("Invalid vars plugin %s from %s" % (plugin._load_name, plugin._original_path))
    return data


def get_plugin_vars(loader, path, entities):

    data = {}
    for plugin in vars_loader.all():
        data = combine_vars(data, _get_vars_from_plugin(plugin, loader, path, entities))

    return data
