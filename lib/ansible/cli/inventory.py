# Copyright: (c) 2017, Brian Coca <bcoca@ansible.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys

import argparse
import pkgutil
import os

from operator import attrgetter

from ansible import constants as C
from ansible import context
from ansible.cli import CLI
from ansible.cli.arguments import option_helpers as opt_help
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.module_utils._text import to_bytes, to_native
from ansible.module_utils.six import string_types
from ansible.template import Templar
from ansible.utils.vars import combine_vars
from ansible.utils.display import Display
from ansible.vars.plugins import get_vars_from_inventory_sources, get_vars_from_path

display = Display()

INTERNAL_VARS = frozenset(['ansible_diff_mode',
                           'ansible_config_file',
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
        opt_help.add_runtask_options(self.parser)

        # remove unused default options
        self.parser.add_argument('-l', '--limit', help=argparse.SUPPRESS, action=opt_help.UnrecognizedArgument, nargs='?')
        self.parser.add_argument('--list-hosts', help=argparse.SUPPRESS, action=opt_help.UnrecognizedArgument)

        self.parser.add_argument('args', metavar='host|group', nargs='?')

        # Actions
        action_group = self.parser.add_argument_group("Actions", "One of following must be used on invocation, ONLY ONE!")
        action_group.add_argument("--list", action="store_true", default=False, dest='list', help='Output all hosts info, works as inventory script')
        action_group.add_argument("--host", action="store", default=None, dest='host', help='Output specific host info, works as inventory script')

        #TODO: deprecate for template
        action_group.add_argument("--graph", action="store_true", default=False, dest='graph',
                                  help='create inventory graph, if supplying pattern it must be a valid group name')
        self.parser.add_argument_group(action_group)

        # graph
        action_group.add_argument("--template", action="store", default='json', dest='template', help='Jinja2 temlpate used to output the result')
        self.parser.add_argument("--vars", action="store_true", default=False, dest='show_vars',
                                 help='Add vars to graph display, ignored unless used with --graph')

        #TODO: deprecate both for template
        self.parser.add_argument("-y", "--yaml", action="store_true", default=False, dest='yaml',
                                 help='Use YAML format instead of default JSON, ignored for --graph')
        self.parser.add_argument('--toml', action='store_true', default=False, dest='toml',
                                 help='Use TOML format instead of default JSON, ignored for --graph')

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
            options.pattern = options.args
        else:
            options.pattern = 'all'

        return options

    def run(self):

        super(InventoryCLI, self).run()

        # Initialize needed objects
        self.loader, self.inventory, self.vm = self._play_prereqs()

        results = None
        template = None
        if context.CLIARGS['host']:
            hosts = self.inventory.get_hosts(context.CLIARGS['host'])
            if len(hosts) != 1:
                raise AnsibleOptionsError("You must pass a single valid host to --host parameter")

            myvars = self._get_host_variables(host=hosts[0])

            # FIXME: should we template first?
            results = self.dump(myvars)

        elif context.CLIARGS['list']:

            if context.CLIARGS['template']:
                template = context.CLIARGS['template']
            elif context.CLIARGS['yaml']:
                template =  'yaml.j2'
            elif context.CLIARGS['toml']:
                template =  'toml.j2'
            else:
                template =  'json.j2'
                #results = self.yaml_inventory(top)
                #results = self.toml_inventory(top)
                #results = self.json_inventory(top)
        elif context.CLIARGS['graph']:
            # TODO: deprecate for template option
            template =  'graph.j2'

        if results is None and template is not None:

            # get top from pattern (default is all)
            top = context.CLIARGS['pattern']
            results = self.dump_templated_results(top, template)

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
            sys.exit(0)

        sys.exit(1)

    def dump_templated_results(self, top, template):

        def format_host(host):
            return {'name': host.name, 'vars': self._get_host_variables(host)}

        def format_group(pgroup):
            if isinstance(pgroup, string_types):
                group = self._get_group(pgroup)

            if group is None:
                raise AnsibleOptionsError("Processing invalid group: %s" % pgroup)

            result = {'name': group.name, 'hosts': [], 'children':[], 'vars': {}}

            if group.name != 'all':
                result['hosts'] = [format_host(h) for h in sorted(group.hosts, key=attrgetter('name'))]

            for subgroup in sorted(group.child_groups, key=attrgetter('name')):
                result['children'].append(format_group(subgroup.name))

            if context.CLIARGS['export']:
                result['vars'] = self._get_group_variables(group)

            return result

        # get template string
        try:
            tstring = ''
            if os.path.isabs(template):
                tstring = open(template).read()
            else:
                # FIXME: not finding/reading data
                for ext in ('' , '.j2'):
                    template = ''.join([template, ext])
                    tstring = pkgutil.get_data('ansible.inventory.templates', template)
                    if tstring:
                        break
        except Exception as e:
            raise AnsibleOptionsError("Invalid template option supplied, could not find a match for '%s': %s" % (template, to_native(e)))

        print(tstring)
        # start data tree
        groups = [format_group(top)]

        # template
        t = Templar(self.loader, variables={'groups': groups, 'export': context.CLIARGS['export']})
        return t.template(tstring)

    def _get_group_variables(self, group):

        # get info from inventory source
        res = group.get_vars()

        # Always load vars plugins
        res = combine_vars(res, get_vars_from_inventory_sources(self.loader, self.inventory._sources, [group], 'all'))
        if context.CLIARGS['basedir']:
            res = combine_vars(res, get_vars_from_path(self.loader, context.CLIARGS['basedir'], [group], 'all'))

        if group.priority != 1:
            res['ansible_group_priority'] = group.priority

        return self._remove_internal(res)

    def _get_host_variables(self, host):

        if context.CLIARGS['export']:
            # only get vars defined directly host
            hostvars = host.get_vars()

            # Always load vars plugins
            hostvars = combine_vars(hostvars, get_vars_from_inventory_sources(self.loader, self.inventory._sources, [host], 'all'))
            if context.CLIARGS['basedir']:
                hostvars = combine_vars(hostvars, get_vars_from_path(self.loader, context.CLIARGS['basedir'], [host], 'all'))
        else:
            # get all vars flattened by host, but skip magic hostvars
            hostvars = self.vm.get_vars(host=host, include_hostvars=False, stage='all')

        return self._remove_internal(hostvars)

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
                if context.CLIARGS['show_vars']:
                    result.extend(self._show_vars(self._get_host_variables(host), depth + 1))

        if context.CLIARGS['show_vars']:
            result.extend(self._show_vars(self._get_group_variables(group), depth))

        return result

    def inventory_graph(self):

        start_at = self._get_group(context.CLIARGS['pattern'])
        if start_at:
            return '\n'.join(self._graph_group(start_at))
        else:
            raise AnsibleOptionsError("Pattern must be valid group name when using --graph")
