#
# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
import re

from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.iosxr.providers.providers import CliProvider


class AddressFamily(CliProvider):

    def render(self, config=None):
        commands = list()
        safe_list = list()

        router_context = 'router bgp %s' % self.get_value('config.bgp_as')
        context_config = None

        for item in self.get_value('config.address_family'):
            context = 'address-family %s %s' % (item['afi'], item['safi'])
            context_commands = list()

            if config:
                context_path = [router_context, context]
                context_config = self.get_config_context(config, context_path, indent=1)

            for key, value in iteritems(item):
                if value is not None:
                    meth = getattr(self, '_render_%s' % key, None)
                    if meth:
                        resp = meth(item, context_config)
                        if resp:
                            context_commands.extend(to_list(resp))

            if context_commands:
                commands.append(context)
                commands.extend(context_commands)
                commands.append('exit')

            safe_list.append(context)

        if config:
            resp = self._negate_config(config, safe_list)
            commands.extend(resp)

        return commands

    def _negate_config(self, config, safe_list=None):
        commands = list()
        matches = re.findall(r'(address-family .+)$', config, re.M)
        for item in set(matches).difference(safe_list):
            commands.append('no %s' % item)
        return commands

    def _render_networks(self, item, config=None):
        commands = list()
        safe_list = list()

        for entry in item['networks']:
            network = entry['prefix']
            if entry['masklen']:
                network = '%s/%s' % (entry['prefix'], entry['masklen'])
            safe_list.append(network)

            cmd = 'network %s' % network

            if entry['route_map']:
                cmd += ' route-policy %s' % entry['route_map']

            if not config or cmd not in config:
                commands.append(cmd)

        if config and self.params['operation'] == 'replace':
            matches = re.findall(r'network (\S+)', config, re.M)
            for entry in set(matches).difference(safe_list):
                commands.append('no network %s' % entry)

        return commands

    def _render_redistribute(self, item, config=None):
        commands = list()
        safe_list = list()

        for entry in item['redistribute']:
            option = entry['protocol']

            cmd = 'redistribute %s' % entry['protocol']

            if entry['id'] and entry['protocol'] in ('ospf', 'eigrp', 'isis', 'ospfv3'):
                cmd += ' %s' % entry['id']
                option += ' %s' % entry['id']

            if entry['metric']:
                cmd += ' metric %s' % entry['metric']

            if entry['route_map']:
                cmd += ' route-policy %s' % entry['route_map']

            if not config or cmd not in config:
                commands.append(cmd)

            safe_list.append(option)

        if self.params['operation'] == 'replace':
            if config:
                matches = re.findall(r'redistribute (\S+)(?:\s*)(\d*)', config, re.M)
                for i in range(0, len(matches)):
                    matches[i] = ' '.join(matches[i]).strip()
                for entry in set(matches).difference(safe_list):
                    commands.append('no redistribute %s' % entry)

        return commands
