# (c) 2017, Brian Coca <bcoca@ansible.com>
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
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import optparse
from operator import attrgetter

from ansible import constants as C
from ansible.cli import CLI
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.inventory.host import Host
from ansible.plugins.loader import vars_loader
from ansible.parsing.dataloader import DataLoader
from ansible.utils.vars import combine_vars

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

INTERNAL_VARS = frozenset(['ansible_diff_mode',
                           'ansible_facts',
                           'ansible_forks',
                           'ansible_inventory_sources',
                           'ansible_limit',
                           'ansible_playbook_python',
                           'ansible_run_tags',
                           'ansible_skip_tags',
                           'ansible_version',
                           'inventory_dir',
                           'inventory_file',
                           'inventory_hostname',
                           'inventory_hostname_short',
                           'groups',
                           'group_names',
                           'omit',
                           'playbook_dir', ])


class InventoryCLI(CLI):
    ''' used to display or dump the configured inventory as Ansible sees it '''

    ARGUMENTS = {'host': 'The name of a host to match in the inventory, relevant when using --list',
                 'group': 'The name of a group in the inventory, relevant when using --graph', }

    def __init__(self, args):

        super(InventoryCLI, self).__init__(args)
        self.vm = None
        self.loader = None
        self.inventory = None

        self._new_api = True

    def parse(self):

        self.parser = CLI.base_parser(
            usage='usage: %prog [options] [host|group]',
            epilog='Show Ansible inventory information, by default it uses the inventory script JSON format',
            inventory_opts=True,
            vault_opts=True,
            basedir_opts=True,
        )

        # remove unused default options
        self.parser.remove_option('--limit')
        self.parser.remove_option('--list-hosts')

        # Actions
        action_group = optparse.OptionGroup(self.parser, "Actions", "One of following must be used on invocation, ONLY ONE!")
        action_group.add_option("--list", action="store_true", default=False, dest='list', help='Output all hosts info, works as inventory script')
        action_group.add_option("--host", action="store", default=None, dest='host', help='Output specific host info, works as inventory script')
        action_group.add_option("--graph", action="store_true", default=False, dest='graph',
                                help='create inventory graph, if supplying pattern it must be a valid group name')
        self.parser.add_option_group(action_group)

        # graph
        self.parser.add_option("-y", "--yaml", action="store_true", default=False, dest='yaml',
                               help='Use YAML format instead of default JSON, ignored for --graph')
        self.parser.add_option("--vars", action="store_true", default=False, dest='show_vars',
                               help='Add vars to graph display, ignored unless used with --graph')

        # list
        self.parser.add_option("--export", action="store_true", default=C.INVENTORY_EXPORT, dest='export',
                               help="When doing an --list, represent in a way that is optimized for export,"
                                    "not as an accurate representation of how Ansible has processed it")
        # self.parser.add_option("--ignore-vars-plugins", action="store_true", default=False, dest='ignore_vars_plugins',
        #                       help="When doing an --list, skip vars data from vars plugins, by default, this would include group_vars/ and host_vars/")

        super(InventoryCLI, self).parse()

        display.verbosity = self.options.verbosity

        self.validate_conflicts(vault_opts=True)

        # there can be only one! and, at least, one!
        used = 0
        for opt in (self.options.list, self.options.host, self.options.graph):
            if opt:
                used += 1
        if used == 0:
            raise AnsibleOptionsError("No action selected, at least one of --host, --graph or --list needs to be specified.")
        elif used > 1:
            raise AnsibleOptionsError("Conflicting options used, only one of --host, --graph or --list can be used at the same time.")

        # set host pattern to default if not supplied
        if len(self.args) > 0:
            self.options.pattern = self.args[0]
        else:
            self.options.pattern = 'all'

    def run(self):

        results = None

        super(InventoryCLI, self).run()

        # Initialize needed objects
        if getattr(self, '_play_prereqs', False):
            self.loader, self.inventory, self.vm = self._play_prereqs(self.options)
        else:
            # fallback to pre 2.4 way of initialzing
            from ansible.vars import VariableManager
            from ansible.inventory import Inventory

            self._new_api = False
            self.loader = DataLoader()
            self.vm = VariableManager()

            # use vault if needed
            if self.options.vault_password_file:
                vault_pass = CLI.read_vault_password_file(self.options.vault_password_file, loader=self.loader)
            elif self.options.ask_vault_pass:
                vault_pass = self.ask_vault_passwords()
            else:
                vault_pass = None

            if vault_pass:
                self.loader.set_vault_password(vault_pass)
                # actually get inventory and vars

            self.inventory = Inventory(loader=self.loader, variable_manager=self.vm, host_list=self.options.inventory)
            self.vm.set_inventory(self.inventory)

        if self.options.host:
            hosts = self.inventory.get_hosts(self.options.host)
            if len(hosts) != 1:
                raise AnsibleOptionsError("You must pass a single valid host to --hosts parameter")

            myvars = self._get_host_variables(host=hosts[0])
            self._remove_internal(myvars)

            # FIXME: should we template first?
            results = self.dump(myvars)

        elif self.options.graph:
            results = self.inventory_graph()
        elif self.options.list:
            top = self._get_group('all')
            if self.options.yaml:
                results = self.yaml_inventory(top)
            else:
                results = self.json_inventory(top)
            results = self.dump(results)

        if results:
            # FIXME: pager?
            display.display(results)
            exit(0)

        exit(1)

    def dump(self, stuff):

        if self.options.yaml:
            import yaml
            from ansible.parsing.yaml.dumper import AnsibleDumper
            results = yaml.dump(stuff, Dumper=AnsibleDumper, default_flow_style=False)
        else:
            import json
            from ansible.parsing.ajson import AnsibleJSONEncoder
            results = json.dumps(stuff, cls=AnsibleJSONEncoder, sort_keys=True, indent=4)

        return results

    # FIXME: refactor to use same for VM
    def get_plugin_vars(self, path, entity):

        data = {}

        def _get_plugin_vars(plugin, path, entities):
            data = {}
            try:
                data = plugin.get_vars(self.loader, path, entity)
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

        for plugin in vars_loader.all():
            data = combine_vars(data, _get_plugin_vars(plugin, path, entity))

        return data

    def _get_group_variables(self, group):

        # get info from inventory source
        res = group.get_vars()

        # FIXME: add switch to skip vars plugins, add vars plugin info
        for inventory_dir in self.inventory._sources:
            res = combine_vars(res, self.get_plugin_vars(inventory_dir, group))

        if group.priority != 1:
            res['ansible_group_priority'] = group.priority

        return res

    def _get_host_variables(self, host):

        if self.options.export:
            hostvars = host.get_vars()

            # FIXME: add switch to skip vars plugins
            # add vars plugin info
            for inventory_dir in self.inventory._sources:
                hostvars = combine_vars(hostvars, self.get_plugin_vars(inventory_dir, host))
        else:
            if self._new_api:
                hostvars = self.vm.get_vars(host=host, include_hostvars=False)
            else:
                hostvars = self.vm.get_vars(self.loader, host=host, include_hostvars=False)

        return hostvars

    def _get_group(self, gname):
        if self._new_api:
            group = self.inventory.groups.get(gname)
        else:
            group = self.inventory.get_group(gname)
        return group

    def _remove_internal(self, dump):

        for internal in INTERNAL_VARS:
            if internal in dump:
                del dump[internal]

    def _remove_empty(self, dump):
        # remove empty keys
        for x in ('hosts', 'vars', 'children'):
            if x in dump and not dump[x]:
                del dump[x]

    def _show_vars(self, dump, depth):
        result = []
        self._remove_internal(dump)
        if self.options.show_vars:
            for (name, val) in sorted(dump.items()):
                result.append(self._graph_name('{%s = %s}' % (name, val), depth))
        return result

    def _graph_name(self, name, depth=0):
        if depth:
            name = "  |" * (depth) + "--%s" % name
        return name

    def _graph_group(self, group, depth=0):

        result = [self._graph_name('@%s:' % group.name, depth)]
        depth = depth + 1
        for kid in sorted(group.child_groups, key=attrgetter('name')):
            result.extend(self._graph_group(kid, depth))

        if group.name != 'all':
            for host in sorted(group.hosts, key=attrgetter('name')):
                result.append(self._graph_name(host.name, depth))
                result.extend(self._show_vars(host.get_vars(), depth + 1))

        result.extend(self._show_vars(self._get_group_variables(group), depth))

        return result

    def inventory_graph(self):

        start_at = self._get_group(self.options.pattern)
        if start_at:
            return '\n'.join(self._graph_group(start_at))
        else:
            raise AnsibleOptionsError("Pattern must be valid group name when using --graph")

    def json_inventory(self, top):

        def format_group(group):
            results = {}
            results[group.name] = {}
            if group.name != 'all':
                results[group.name]['hosts'] = [h.name for h in sorted(group.hosts, key=attrgetter('name'))]
            results[group.name]['children'] = []
            for subgroup in sorted(group.child_groups, key=attrgetter('name')):
                results[group.name]['children'].append(subgroup.name)
                results.update(format_group(subgroup))
            if self.options.export:
                results[group.name]['vars'] = self._get_group_variables(group)

            self._remove_empty(results[group.name])

            return results

        results = format_group(top)

        # populate meta
        results['_meta'] = {'hostvars': {}}
        hosts = self.inventory.get_hosts()
        for host in hosts:
            hvars = self._get_host_variables(host)
            if hvars:
                self._remove_internal(hvars)
                results['_meta']['hostvars'][host.name] = hvars

        return results

    def yaml_inventory(self, top):

        seen = []

        def format_group(group):
            results = {}

            # initialize group + vars
            results[group.name] = {}

            # subgroups
            results[group.name]['children'] = {}
            for subgroup in sorted(group.child_groups, key=attrgetter('name')):
                if subgroup.name != 'all':
                    results[group.name]['children'].update(format_group(subgroup))

            # hosts for group
            results[group.name]['hosts'] = {}
            if group.name != 'all':
                for h in sorted(group.hosts, key=attrgetter('name')):
                    myvars = {}
                    if h.name not in seen:  # avoid defining host vars more than once
                        seen.append(h.name)
                        myvars = self._get_host_variables(host=h)
                        self._remove_internal(myvars)
                    results[group.name]['hosts'][h.name] = myvars

            if self.options.export:

                gvars = self._get_group_variables(group)
                if gvars:
                    results[group.name]['vars'] = gvars

            self._remove_empty(results[group.name])

            return results

        return format_group(top)
