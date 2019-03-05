# Copyright: (c) 2017, Brian Coca <bcoca@ansible.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import optparse
from operator import attrgetter

from ansible import constants as C
from ansible import context
from ansible.cli import CLI
from ansible.cli.arguments import optparse_helpers as opt_help
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.inventory.host import Host
from ansible.module_utils._text import to_bytes, to_native
from ansible.plugins.loader import vars_loader
from ansible.utils.vars import combine_vars
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
                           'ansible_verbosity',
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

    def init_parser(self):
        super(InventoryCLI, self).init_parser(
            usage='usage: %prog [options] [host|group]',
            epilog='Show Ansible inventory information, by default it uses the inventory script JSON format')

        opt_help.add_inventory_options(self.parser)
        opt_help.add_vault_options(self.parser)
        opt_help.add_basedir_options(self.parser)

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
        self.parser.add_option('--toml', action='store_true', default=False, dest='toml',
                               help='Use TOML format instead of default JSON, ignored for --graph')
        self.parser.add_option("--vars", action="store_true", default=False, dest='show_vars',
                               help='Add vars to graph display, ignored unless used with --graph')

        # list
        self.parser.add_option("--export", action="store_true", default=C.INVENTORY_EXPORT, dest='export',
                               help="When doing an --list, represent in a way that is optimized for export,"
                                    "not as an accurate representation of how Ansible has processed it")
        self.parser.add_option('--output', default=None, dest='output_file',
                               help="When doing an --list, send the inventory to a file instead of of to screen")
        # self.parser.add_option("--ignore-vars-plugins", action="store_true", default=False, dest='ignore_vars_plugins',
        #                       help="When doing an --list, skip vars data from vars plugins, by default, this would include group_vars/ and host_vars/")

    def post_process_args(self, options, args):
        options, args = super(InventoryCLI, self).post_process_args(options, args)

        display.verbosity = options.verbosity
        self.validate_conflicts(options, vault_opts=True)

        # there can be only one! and, at least, one!
        used = 0
        for opt in (options.list, options.host, options.graph):
            if opt:
                used += 1
        if used == 0:
            raise AnsibleOptionsError("No action selected, at least one of --host, --graph or --list needs to be specified.")
        elif used > 1:
            raise AnsibleOptionsError("Conflicting options used, only one of --host, --graph or --list can be used at the same time.")

        # set host pattern to default if not supplied
        if len(args) > 0:
            options.pattern = args[0]
        else:
            options.pattern = 'all'

        return options, args

    def run(self):

        super(InventoryCLI, self).run()

        # Initialize needed objects
        self.loader, self.inventory, self.vm = self._play_prereqs()

        results = None
        if context.CLIARGS['host']:
            hosts = self.inventory.get_hosts(context.CLIARGS['host'])
            if len(hosts) != 1:
                raise AnsibleOptionsError("You must pass a single valid host to --host parameter")

            myvars = self._get_host_variables(host=hosts[0])
            self._remove_internal(myvars)

            # FIXME: should we template first?
            results = self.dump(myvars)

        elif context.CLIARGS['graph']:
            results = self.inventory_graph()
        elif context.CLIARGS['list']:
            top = self._get_group('all')
            if context.CLIARGS['yaml']:
                results = self.yaml_inventory(top)
            elif context.CLIARGS['toml']:
                results = self.toml_inventory(top)
            else:
                results = self.json_inventory(top)
            results = self.dump(results)

        if results:
            outfile = context.CLIARGS['output_file']
            if outfile is None:
                # FIXME: pager?
                display.display(results)
            else:
                try:
                    with open(to_bytes(outfile), 'wt') as f:
                        f.write(results)
                except (OSError, IOError) as e:
                    raise AnsibleError('Unable to write to destination file (%s): %s' % (to_native(outfile), to_native(e)))
            exit(0)

        exit(1)

    @staticmethod
    def dump(stuff):

        if context.CLIARGS['yaml']:
            import yaml
            from ansible.parsing.yaml.dumper import AnsibleDumper
            results = yaml.dump(stuff, Dumper=AnsibleDumper, default_flow_style=False)
        elif context.CLIARGS['toml']:
            from ansible.plugins.inventory.toml import toml_dumps, HAS_TOML
            if not HAS_TOML:
                raise AnsibleError(
                    'The python "toml" library is required when using the TOML output format'
                )
            results = toml_dumps(stuff)
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

        if context.CLIARGS['export']:
            hostvars = host.get_vars()

            # FIXME: add switch to skip vars plugins
            # add vars plugin info
            for inventory_dir in self.inventory._sources:
                hostvars = combine_vars(hostvars, self.get_plugin_vars(inventory_dir, host))
        else:
            hostvars = self.vm.get_vars(host=host, include_hostvars=False)

        return hostvars

    def _get_group(self, gname):
        group = self.inventory.groups.get(gname)
        return group

    @staticmethod
    def _remove_internal(dump):

        for internal in INTERNAL_VARS:
            if internal in dump:
                del dump[internal]

    @staticmethod
    def _remove_empty(dump):
        # remove empty keys
        for x in ('hosts', 'vars', 'children'):
            if x in dump and not dump[x]:
                del dump[x]

    @staticmethod
    def _show_vars(dump, depth):
        result = []
        InventoryCLI._remove_internal(dump)
        if context.CLIARGS['show_vars']:
            for (name, val) in sorted(dump.items()):
                result.append(InventoryCLI._graph_name('{%s = %s}' % (name, val), depth))
        return result

    @staticmethod
    def _graph_name(name, depth=0):
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

        start_at = self._get_group(context.CLIARGS['pattern'])
        if start_at:
            return '\n'.join(self._graph_group(start_at))
        else:
            raise AnsibleOptionsError("Pattern must be valid group name when using --graph")

    def json_inventory(self, top):

        seen = set()

        def format_group(group):
            results = {}
            results[group.name] = {}
            if group.name != 'all':
                results[group.name]['hosts'] = [h.name for h in sorted(group.hosts, key=attrgetter('name'))]
            results[group.name]['children'] = []
            for subgroup in sorted(group.child_groups, key=attrgetter('name')):
                results[group.name]['children'].append(subgroup.name)
                if subgroup.name not in seen:
                    results.update(format_group(subgroup))
                    seen.add(subgroup.name)
            if context.CLIARGS['export']:
                results[group.name]['vars'] = self._get_group_variables(group)

            self._remove_empty(results[group.name])
            if not results[group.name]:
                del results[group.name]

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

            if context.CLIARGS['export']:
                gvars = self._get_group_variables(group)
                if gvars:
                    results[group.name]['vars'] = gvars

            self._remove_empty(results[group.name])

            return results

        return format_group(top)

    def toml_inventory(self, top):
        seen = set()
        has_ungrouped = bool(next(g.hosts for g in top.child_groups if g.name == 'ungrouped'))

        def format_group(group):
            results = {}
            results[group.name] = {}

            results[group.name]['children'] = []
            for subgroup in sorted(group.child_groups, key=attrgetter('name')):
                if subgroup.name == 'ungrouped' and not has_ungrouped:
                    continue
                if group.name != 'all':
                    results[group.name]['children'].append(subgroup.name)
                results.update(format_group(subgroup))

            if group.name != 'all':
                for host in sorted(group.hosts, key=attrgetter('name')):
                    if host.name not in seen:
                        seen.add(host.name)
                        host_vars = self._get_host_variables(host=host)
                        self._remove_internal(host_vars)
                    else:
                        host_vars = {}
                    try:
                        results[group.name]['hosts'][host.name] = host_vars
                    except KeyError:
                        results[group.name]['hosts'] = {host.name: host_vars}

            if context.CLIARGS['export']:
                results[group.name]['vars'] = self._get_group_variables(group)

            self._remove_empty(results[group.name])
            if not results[group.name]:
                del results[group.name]

            return results

        results = format_group(top)

        return results
