# Copyright: (c) 2017, Brian Coca <bcoca@ansible.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import argparse
from operator import attrgetter
from pprint import pformat

from ansible import constants as C
from ansible import context
from ansible.cli import CLI
from ansible.cli.arguments import option_helpers as opt_help
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.inventory.helpers import sort_groups
from ansible.module_utils._text import to_bytes, to_native
from ansible.module_utils.common._collections_compat import MutableMapping
from ansible.plugins.loader import vars_loader
from ansible.utils.vars import combine_vars
from ansible.utils.display import Display
from ansible.utils.color import stringc

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
        self.parser.add_argument('--limit', default=argparse.SUPPRESS, type=lambda v: self.parser.error('unrecognized arguments: --limit'))
        self.parser.add_argument('--list-hosts', default=argparse.SUPPRESS, type=lambda v: self.parser.error('unrecognized arguments: --list-hosts'))

        self.parser.add_argument('args', metavar='host|group', nargs='?')

        # Actions
        action_group = self.parser.add_argument_group("Actions", "One of following must be used on invocation, ONLY ONE!")
        action_group.add_argument("--list", action="store_true", default=False, dest='list', help='Output all hosts info, works as inventory script')
        action_group.add_argument("--host", action="store", default=None, dest='host', help='Output specific host info, works as inventory script')
        action_group.add_argument("--graph", action="store_true", default=False, dest='graph',
                                  help='create inventory graph, if supplying pattern it must be a valid group name')
        self.parser.add_argument_group(action_group)

        # host
        self.parser.add_argument("--unmerge", action="store_true", default=False,
                                 help='Show all vars before merging, ignored unless used with --host')
        self.parser.add_argument("--filter", action="store",
                                 help='Show only vars whose path contains FILTER, ignored unless used with --unmerge')

        # graph
        self.parser.add_argument("-y", "--yaml", action="store_true", default=False, dest='yaml',
                                 help='Use YAML format instead of default JSON, ignored for --graph')
        self.parser.add_argument('--toml', action='store_true', default=False, dest='toml',
                                 help='Use TOML format instead of default JSON, ignored for --graph')
        self.parser.add_argument("--vars", action="store_true", default=False, dest='show_vars',
                                 help='Add vars to graph display, ignored unless used with --graph')

        # list
        self.parser.add_argument("--export", action="store_true", default=C.INVENTORY_EXPORT, dest='export',
                                 help="When doing an --list, represent in a way that is optimized for export,"
                                      "not as an accurate representation of how Ansible has processed it")
        self.parser.add_argument('--output', default=None, dest='output_file',
                                 help="When doing --list, send the inventory to a file instead of to the screen")
        # self.parser.add_argument("--ignore-vars-plugins", action="store_true", default=False, dest='ignore_vars_plugins',
        #                          help="When doing an --list, skip vars data from vars plugins, by default, this would include group_vars/ and host_vars/")

    def post_process_args(self, options):
        options = super(InventoryCLI, self).post_process_args(options)

        display.verbosity = options.verbosity
        self.validate_conflicts(options)

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
        if options.args:
            options.pattern = options.args[0]
        else:
            options.pattern = 'all'

        return options

    def run(self):

        super(InventoryCLI, self).run()

        # Initialize needed objects
        self.loader, self.inventory, self.vm = self._play_prereqs()

        results = None
        if context.CLIARGS['host']:
            hosts = self.inventory.get_hosts(context.CLIARGS['host'])
            if len(hosts) != 1:
                raise AnsibleOptionsError("You must pass a single valid host to --host parameter")
            
            if context.CLIARGS['unmerge']:
                myvars = self._get_host_variables_unmerged(host=hosts[0])

                results = self._format_unmerged_variables(myvars)
            else:
                myvars = self._get_host_variables(host=hosts[0])

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

        return self._remove_internal(res)

    def _get_host_variables(self, host, only=False):

        if context.CLIARGS['export'] or only:
            # only get vars defined directly host
            hostvars = host.get_vars()

            # FIXME: add switch to skip vars plugins, add vars plugin info
            for inventory_dir in self.inventory._sources:
                hostvars = combine_vars(hostvars, self.get_plugin_vars(inventory_dir, host))
        else:
            # get all vars flattened by host, but skip magic hostvars
            hostvars = self.vm.get_vars(host=host, include_hostvars=False)

        return self._remove_internal(hostvars)

    def _get_host_variables_unmerged(self, host):
        ''' Build a dict of all host and group variables where :
            - keys are the "flattened paths" of the variables (similar to the dotted format used in jinja templates)
            - values are lists of 2 elements tuples where :
                - first element of the tuple is the "source" (group or host object) where the variable value was found
                - second element of the tuple is the value we found
                - first item of the list is the one that would "win" the merging process
            "Unmerged" because, contrary to 'combine_vars()', we keep values that would have been overwritten.
            The result is something like this :
            {'path.to.variable': [(Host, 123), (Group1, 456), (Group2, 789)]}
        '''

        results = {}
        if C.DEFAULT_HASH_BEHAVIOUR != "merge":
            raise AnsibleOptionsError("--unmerged is only supported when 'hash_behaviour' is set to 'merge'")

        # The following is a simplified version of Ansible's variables precedence system, using only group vars and host vars
        host_groups = sort_groups(host.get_groups())  # Groups are sorted from less specific ('all') to more specific
        for group in host_groups:
            self._combine_vars_unmerged(results, self._get_group_variables(group), group, [])  # Update 'results' with the group's variables
        self._combine_vars_unmerged(results, self._get_host_variables(host, only=True), host, [])  # Lastly, update 'results' with hosts variables
        return results

    @staticmethod
    def _combine_vars_unmerged(results, hash_to_integrate, group, path):
        ''' Recursive function that browses a recursive dict ('hash_to_integrate') to update the 'results' dict.
            For each leaf encountered (i.e. anything that is not another dict) it creates an entry in 'results' with the path (in a dotted format) as key and a list as value.
            This list contain the leaf's value, along with the "source" (group name most of the time, or host name) of 'hash_to_integrate'.
            If the key already exists, the list is simply prepended. The first item of said list is considered to be the "winning" value.
        '''

        for key, value in hash_to_integrate.items():
            new_path = path + [key]
            flattened_path = '.'.join(new_path)
            if isinstance(value, MutableMapping):  # We are not at a leaf
                if flattened_path in results: del results[flattened_path]  # If there was a leaf here previously, delete it as it would have been overwritten by combine_vars
                                                                           # We should maybe find a way to display that...
                InventoryCLI._combine_vars_unmerged(results, value, group, new_path)  # We need to go deeper !
            else:
                if flattened_path in results:
                    results[flattened_path].insert(0, (group, value))  # New value, with higher priority
                else:
                    results[flattened_path] = [(group, value)]  # First time we find a leaf here

    @staticmethod
    def _format_unmerged_variables(unmerged_vars):
        ''' Display the unmerged vars in a human readable way.'''
        source_entities = set()  # A set of all groups where we found vars (and the host if we have hostvars)
        host = None
        for path, values in unmerged_vars.items():
            for source, value in values:
                if isinstance(source, Host) and host is None:
                    host = source
                elif isinstance(source, Group):
                    source_entities.add(source)  # set.add() only adds if item is not present already
        source_entities = sort_groups(source_entities)  # This is now a list of groups with the less specific ('all' for instance) first
        if host is not None: source_entities.append(host)
        source_entities.reverse()  # We're done, we have a list of all place where we found variables, from more specific to less specific

        max_width = len(str(max(source_entities, key=lambda v: len(str(v)))))  # The maximum string length of all group names (and the hostname), for display purposes

        result = []
        for key, values in sorted(unmerged_vars.items()):
            if context.CLIARGS['filter'] is None or context.CLIARGS['filter'] in key:  # Apply filter if provided
                if len(values)==1:  # There was no override, just display "[source] path.to.variable : value"
                    prefix = '[{}] {} : '.format(InventoryCLI._colorize_entity(values[0][0], source_entities, max_width), key)
                    prefix_nocolor = '[{}] {} : '.format(InventoryCLI._colorize_entity(values[0][0], source_entities, max_width, force_nocolor=True), key)
                    value_pretty = pformat(values[0][1]).split('\n')

                    # Add the prefix to the first line. If the value is complex, pprint.pformat() will output multiple lines : in that case, indent the remaining ones.
                    result.extend([prefix + line if index == 0 else " " * len(prefix_nocolor) + line for index, line in enumerate(value_pretty)])

                else:  # There was several candidates, display the winning one first, and then all of them in order (starting with the winning one) along with their source
                    prefix = '[{}] {} : '.format('+' * max_width, key)
                    value_pretty = pformat(values[0][1]).split('\n')

                    # Add the prefix to the first line. If the value is complex, pprint.pformat() will output multiple lines : in that case, indent the remaining ones.
                    result.extend([prefix + line if index == 0 else " " * len(prefix) + line for index, line in enumerate(value_pretty)])

                    local_max_width = len(str(max(values, key=lambda v: len(str(v[0])))[0]))  # Longer of all candidates' sources, for alignment
                    for entity, value in values:
                        prefix = '----[{}] : '.format(InventoryCLI._colorize_entity(entity, source_entities, local_max_width))
                        prefix_nocolor = '----[{}] : '.format(InventoryCLI._colorize_entity(entity, source_entities, local_max_width, force_nocolor=True))
                        value_pretty = pformat(value).split('\n')

                        result.extend([prefix + line if index == 0 else " " * len(prefix_nocolor) + line for index, line in enumerate(value_pretty)])
        return '\n'.join(result)

    @staticmethod
    def _colorize_entity(entity, all_entities, max_width, force_nocolor=False):
        ''' Colorize a Host or Group object in a deterministic way. Returns a colorized string (or not colorized, this is handled in ansible.utils.color) '''
        colors = ['blue', 'green', 'cyan', 'red', 'purple', 'yellow', 'magenta']  # Colors from ansible.utils.color.codeCodes
        color_index = all_entities.index(entity) % len(colors)

        if force_nocolor:
            entity_str = str(entity)
        else:
            entity_str = stringc(str(entity), colors[color_index])

        padding = max_width - len(str(entity))
        return ' ' * padding + entity_str

    def _get_group(self, gname):
        group = self.inventory.groups.get(gname)
        return group

    @staticmethod
    def _remove_internal(dump):

        for internal in INTERNAL_VARS:
            if internal in dump:
                del dump[internal]

        return dump

    @staticmethod
    def _remove_empty(dump):
        # remove empty keys
        for x in ('hosts', 'vars', 'children'):
            if x in dump and not dump[x]:
                del dump[x]

    @staticmethod
    def _show_vars(dump, depth):
        result = []
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
                result.extend(self._show_vars(self._get_host_variables(host), depth + 1))

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
