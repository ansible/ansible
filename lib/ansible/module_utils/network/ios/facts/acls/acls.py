#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_acls fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from copy import deepcopy
import re
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.ios.utils.utils import check_n_return_valid_ipv6_addr
from ansible.module_utils.network.ios.argspec.acls.acls import AclsArgs


class AclsFacts(object):
    """ The ios_acls fact class
    """

    def __init__(self, module, subspec='config', options='options'):

        self._module = module
        self.argument_spec = AclsArgs.argument_spec
        spec = deepcopy(self.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = utils.generate_dict(facts_argument_spec)

    def get_acl_data(self, connection):
        # Get the access-lists from the ios router
        return connection.get('sh access-list')

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for acls
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """

        if not data:
            data = self.get_acl_data(connection)
        # operate on a collection of resource x
        config = data.split('\n')
        spec = {'acls': list(), 'afi': None}
        if config:
            objs = self.render_config(spec, config)
        # check if rendered config list has only empty dict
        if len(objs) == 1 and objs[0] == {}:
            objs = []
        facts = {}

        if objs:
            facts['acls'] = []
            params = utils.validate_config(self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['acls'].append(utils.remove_empties(cfg))
        ansible_facts['ansible_network_resources'].update(facts)

        return ansible_facts

    def create_config_dict(self, config):
        """ Function that parse the acls config and convert to module usable config
        :param config: config
        :rtype: A dict
        :returns: the config generated based on have config params
        """
        conf = {}
        temp_list = []
        access_list_name = ''
        count = 0
        if len(config) >= 1 and config[0] != '':
            for each in config:
                if 'access-list' in each:
                    temp = each.split('access-list ')[1].split(' ')[0]
                    if temp == 'extended' or temp == 'standard':
                        temp = each.split('access-list ')[1]
                if not access_list_name:
                    access_list_name = temp
                if 'access-list' not in each:
                    if 'extended' in temp or 'standard' in temp:
                        temp_list.append('ipv4 access-list ' + temp + each)
                    else:
                        temp_list.append('ipv6 access-list ' + temp + each)
                if temp == access_list_name and 'access-list' in each and \
                        not ('extended' in access_list_name or 'standard' in access_list_name):
                    temp_list.append(each)
                elif temp != access_list_name:
                    conf[access_list_name] = temp_list
                    temp_list = list()
                    if 'permit' in each or 'deny' in each:
                        temp_list.append(each)
                    access_list_name = temp
                count += 1
                if len(config) == count:
                    conf[access_list_name] = temp_list
                    temp_list = []
        return conf

    def populate_port_protocol(self, source, destination, each_list):
        """ Function Populates port portocol wrt to source and destination
        :param acls: source config
        :param config: destination config
        :param each_list: config
        :rtype: A list
        :returns: the commands generated based on source and destination params
        """
        operators = ['eq', 'gt', 'lt', 'neq', 'range']
        for item in operators:
            if item in each_list:
                index = each_list.index(item)
                if source.get('address') or source.get('any') or source.get('host') and not source.get('port_protocol'):
                    try:
                        source_index = each_list.index(source.get('address'))
                    except ValueError:
                        try:
                            source_index = each_list.index('any')
                        except ValueError:
                            source_index = each_list.index('host')
                    if source.get('address'):
                        if (source_index + 2) == index and 'ipv6' not in each_list:
                            source['port_protocol'] = {item: each_list[index + 1]}
                            each_list.remove(item)
                            del each_list[index]
                        elif (source_index + 1) == index and 'ipv6' in each_list:
                            source['port_protocol'] = {item: each_list[index + 1]}
                            each_list.remove(item)
                            del each_list[source_index]
                            del each_list[index - 1]
                    elif source.get('any'):
                        if (source_index + 1) == index:
                            source['port_protocol'] = {item: each_list[index + 1]}
                            each_list.remove(item)
                            del each_list[index - 1]
                            del each_list[source_index]
                    elif source.get('host'):
                        if (source_index + 1) == index:
                            source['port_protocol'] = {item: each_list[index + 1]}
                            each_list.remove(item)
                            del each_list[index - 1]
                        del each_list[source_index]
                if destination.get('address') or destination.get('any') or destination.get('host'):
                    try:
                        destination_index = each_list.index(destination.get('address'))
                    except ValueError:
                        try:
                            destination_index = each_list.index('any')
                        except ValueError:
                            destination_index = each_list.index('host') + 1
                            index -= 1
                    if (destination_index + 1) == index or (destination_index + 2) == index:
                        destination['port_protocol'] = {item: each_list[index + 1]}
                        each_list.remove(item)
                        del each_list[index]
                break
        if 'eq' in each_list or 'gt' in each_list or 'lt' in each_list or 'neq' in each_list or 'range' in each_list:
            self.populate_port_protocol(source, destination, each_list)

    def populate_source_destination(self, each, config, source, destination):
        any = []
        if 'any' in each:
            any = re.findall('any', each)
            if len(any) == 2:
                source['any'] = True
                destination['any'] = True
        elif 'host' in each:
            host = re.findall('host', each)
            each = each.split(' ')
            if len(host) == 2:
                host_index = each.index('host')
                source['host'] = each[host_index + 1]
                del each[host_index]
                host_index = each.index('host')
                destination['host'] = each[host_index + 1]
            else:
                ip_n_wildcard_bits = re.findall(r'[0-9]+(?:\.[0-9]+){3}', each)
                ip_index = None
                if ip_n_wildcard_bits:
                    ip_index = each.index(ip_n_wildcard_bits[0])
                host_index = each.index('host')
                if ip_index:
                    if host_index < ip_index:
                        source['host'] = each(host_index + 1)
                        destination['address'] = ip_n_wildcard_bits[0]
                        destination['wildcard_bits'] = ip_n_wildcard_bits[1]
                    elif host_index > ip_index:
                        destination['host'] = each(host_index + 1)
                        source['address'] = ip_n_wildcard_bits[0]
                        source['wildcard_bits'] = ip_n_wildcard_bits[1]
        else:
            if config['afi'] == 'ipv4':
                ip_n_wildcard_bits = re.findall(r'[0-9]+(?:\.[0-9]+){3}', each)
                each = each.split(' ')
                if len(ip_n_wildcard_bits) == 0 and len(any) == 1:
                    source['any'] = True
                elif len(ip_n_wildcard_bits) == 1:
                    source['address'] = ip_n_wildcard_bits[0]
                elif len(ip_n_wildcard_bits) == 2:
                    if 'any' in each:
                        if each.index('any') > each.index(ip_n_wildcard_bits[0]):
                            source['address'] = ip_n_wildcard_bits[0]
                            source['wildcard_bits'] = ip_n_wildcard_bits[1]
                            destination['any'] = True
                        elif each.index('any') < each.index(ip_n_wildcard_bits[0]):
                            source['any'] = True
                            destination['address'] = ip_n_wildcard_bits[0]
                            destination['wildcard_bits'] = ip_n_wildcard_bits[1]
                    else:
                        source['address'] = ip_n_wildcard_bits[0]
                        source['wildcard_bits'] = ip_n_wildcard_bits[1]
                elif len(ip_n_wildcard_bits) == 4:
                    source['address'] = ip_n_wildcard_bits[0]
                    source['wildcard_bits'] = ip_n_wildcard_bits[1]
                    destination['address'] = ip_n_wildcard_bits[2]
                    destination['wildcard_bits'] = ip_n_wildcard_bits[3]
            elif config['afi'] == 'ipv6':
                temp_ipv6 = []
                each = each.split(' ')
                check_n_return_valid_ipv6_addr(self._module, each, temp_ipv6)
                count = 0
                for every in each:
                    if len(temp_ipv6) == 2:
                        if temp_ipv6[0] in every or temp_ipv6[1] in every:
                            temp_ipv6[count] = every
                            count += 1
                    elif len(temp_ipv6) == 1:
                        if temp_ipv6[0] in every:
                            temp_ipv6[count] = every
                if 'any' in each:
                    if each.index('any') > each.index(temp_ipv6[0]):
                        source['address'] = temp_ipv6[0]
                        destination['any'] = True
                    elif each.index('any') < each.index(temp_ipv6[0]):
                        source['any'] = True
                        destination['address'] = temp_ipv6[0]
                elif len(temp_ipv6) == 2:
                    source['address'] = temp_ipv6[0]
                    destination['address'] = temp_ipv6[1]

    def parsed_config_facts(self, have_config):
        """
        For parsed config have_config is string of commands which
        need to be splitted before passing it through render_config
        from spec for null values
        :param have_config: The configuration
        :rtype: list of have config
        :returns: The splitted generated config
        """
        split_config = re.split('ip|ipv6 access-list', have_config[0])
        temp_config = []

        # common piece of code for populating the temp_config list
        def common_config_code(each, grant, temp_config):
            temp = re.split(grant, each)
            temp_config.append(temp[0])
            temp_config.extend([grant + item for item in temp if 'access-list' not in item])

        for each in split_config:
            if 'v6' in each:
                each = 'ipv6 ' + each.split('v6 ')[1]
                if 'permit' in each:
                    common_config_code(each, 'permit', temp_config)
                elif 'deny' in each:
                    common_config_code(each, 'deny', temp_config)
            else:
                each = 'ip' + each
                if 'permit' in each:
                    common_config_code(each, 'permit', temp_config)
                if 'deny' in each:
                    common_config_code(each, 'deny', temp_config)
        return temp_config

    def render_config(self, spec, have_config):
        """
        Render config as dictionary structure and delete keys
          from spec for null values
        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """

        # for parsed scnenario where commands are passed to generate the acls facts
        if len(have_config) == 1:
            have_config = self.parsed_config_facts(have_config)

        config = deepcopy(spec)
        render_config = list()
        acls = dict()
        aces = list()
        temp_name = ''
        for each in have_config:
            each_list = [val for val in each.split(' ') if val != '']
            if 'IPv6' in each or 'ipv6' in each:
                if aces:
                    config['acls'].append(acls)
                ip_config = config
                if ip_config.get('acls'):
                    render_config.append(ip_config)
                if not config['afi'] or config['afi'] == 'ipv4':
                    config = deepcopy(spec)
                    config['afi'] = 'ipv6'
                acls = dict()
                aces = list()
            elif not config['afi'] and ('IP' in each or 'ip' in each):
                config['afi'] = 'ipv4'
            if 'access list' in each or 'access-list' in each:
                try:
                    temp_index = each_list.index('list')
                    name = (each_list[temp_index + 1])
                except ValueError:
                    name = each_list[-1]
                if temp_name != name:
                    if aces:
                        config['acls'].append(acls)
                        acls = dict()
                        aces = list()
                    temp_name = name
                acls['name'] = name
            if 'Extended' in each:
                acls['acl_type'] = 'extended'
                continue
            elif 'Standard' in each:
                acls['acl_type'] = 'standard'
                continue
            ace_options = {}
            try:
                if config['afi'] == 'ipv4':
                    if 'deny' in each_list or 'permit' in each_list:
                        ace_options['sequence'] = int(each_list[0])
                elif config['afi'] == 'ipv6':
                    if 'sequence' in each_list:
                        ace_options['sequence'] = int(each_list[each_list.index('sequence') + 1])
            except ValueError:
                pass
            if utils.parse_conf_arg(each, 'permit'):
                ace_options['grant'] = 'permit'
                each_list.remove('permit')
            elif utils.parse_conf_arg(each, 'deny'):
                ace_options['grant'] = 'deny'
                each_list.remove('deny')

            protocol_option = ['ahp', 'eigrp', 'esp', 'gre', 'hbh', 'icmp', 'igmp', 'ip', 'ipv6', 'ipinip', 'nos',
                               'ospf', 'pcp', 'pim', 'sctp', 'tcp', 'udp']
            tcp_flags = ['ack', 'established', 'fin', 'psh', 'rst', 'syn', 'urg']
            icmp_options = ['administratively_prohibited', 'alternate_address', 'conversion_error',
                            'dod_host_prohibited', 'dod_net_prohibited', 'echo', 'echo_reply',
                            'general_parameter_problem', 'host_isolated', 'host_precedence_unreachable',
                            'host_redirect', 'host_tos_redirect', 'host_tos_unreachable', 'host_unknown',
                            'host_unreachable', 'information_reply', 'information_request', 'mask_reply',
                            'mask_request', 'mobile_redirect', 'net_redirect', 'net_tos_redirect',
                            'net_tos_unreachable', 'net_unreachable', 'network_unknown', 'no_room_for_option',
                            'option_missing', 'packet_too_big', 'parameter_problem', 'port_unreachable',
                            'precedence_unreachable', 'protocol_unreachable', 'reassembly_timeout', 'redirect',
                            'router_advertisement', 'router_solicitation', 'source_quench', 'source_route_failed',
                            'time_exceeded', 'timestamp_reply', 'timestamp_request', 'traceroute', 'ttl_exceeded',
                            'unreachable']
            igmp_options = ['dvmrp', 'host_query', 'mtrace_resp', 'mtrace_route', 'pim', 'trace', 'v1host_report',
                            'v2host_report', 'v2leave_group', 'v3host_report']

            temp_option = ''
            for option in protocol_option:
                if option in each_list and 'access' not in each_list[each_list.index(option) + 1]:
                    temp_option = option
                    each_list.remove(temp_option)
                    if temp_option == 'tcp':
                        temp_flag = [each_flag for each_flag in tcp_flags if each_flag in each]
                        if temp_flag:
                            flag = temp_flag[0]
                            if flag in each_list:
                                each_list.remove(flag)
                            temp_flag = flag
                    if temp_option == 'icmp':
                        temp_flag = [each_option for each_option in icmp_options if each_option in each]
                        if temp_flag:
                            flag = temp_flag[0]
                            if flag in each_list:
                                each_list.remove(flag)
                            temp_flag = flag
                    if temp_option == 'igmp':
                        temp_flag = [each_option for each_option in igmp_options if each_option in each]
                        if temp_flag:
                            flag = temp_flag[0]
                            if flag in each_list:
                                each_list.remove(flag)
                            temp_flag = flag
                    break

            dscp = utils.parse_conf_arg(each, 'dscp')
            if dscp:
                ace_options['dscp'] = dscp.split(' ')[0]
            fragments = utils.parse_conf_arg(each, 'fragments')
            if fragments:
                ace_options['fragments'] = fragments.split(' ')[0]
            log = utils.parse_conf_arg(each, 'log')
            if log:
                ace_options['log'] = log.split(' ')[0]
            log_input = utils.parse_conf_arg(each, 'log_input')
            if log_input:
                ace_options['log_input'] = log_input.split(' ')[0]
            option = utils.parse_conf_arg(each, 'option')
            if option:
                option = option.split(' ')[0]
                option_dict = {}
                option_dict[option] = True
                ace_options['option'] = option_dict
            precedence = utils.parse_conf_arg(each, 'precedence')
            if precedence:
                ace_options['precedence'] = precedence.split(' ')[0]
            time_range = utils.parse_conf_arg(each, 'time_range')
            if time_range:
                ace_options['time_range'] = time_range.split(' ')[0]
            tos = utils.parse_conf_arg(each, 'tos')
            if tos:
                tos_val = dict()
                try:
                    tos_val['service_value'] = int(tos)
                except ValueError:
                    tos = tos.replace('-', '_')
                    tos_val[tos] = True
                ace_options['tos'] = tos_val
            ttl = utils.parse_conf_arg(each, 'ttl')
            if ttl:
                temp_ttl = ttl.split(' ')
                ttl = {}
                ttl[temp_ttl[0]] = temp_ttl[1]
                each_list = [item for item in each_list[:each_list.index('ttl')]]
                ace_options['ttl'] = ttl

            source = {}
            destination = {}
            self.populate_source_destination(each, config, source, destination)

            if source.get('address') and source.get('address') == destination.get('address'):
                self._module.fail_json(msg='Source and Destination address cannot be same!')
            else:
                self.populate_port_protocol(source, destination, each_list)

            if source:
                ace_options['source'] = source
            if destination:
                ace_options['destination'] = destination
            if temp_option:
                protocol_options = {}
                ace_options['protocol'] = temp_option
                if temp_option == 'tcp':
                    tcp = {}
                    if temp_flag:
                        tcp[temp_flag] = True
                    else:
                        tcp['set'] = True
                    protocol_options[temp_option] = tcp
                elif temp_option == 'icmp':
                    icmp = dict()
                    if temp_flag:
                        icmp[temp_flag] = True
                    else:
                        icmp['set'] = True
                    protocol_options[temp_option] = icmp
                elif temp_option == 'igmp':
                    igmp = dict()
                    if temp_flag:
                        igmp[temp_flag] = True
                    else:
                        igmp['set'] = True
                    protocol_options[temp_option] = igmp
                else:
                    protocol_options[temp_option] = True
                ace_options['protocol_options'] = protocol_options
            if ace_options:
                aces.append(ace_options)
                acls['aces'] = aces
        if acls:
            if not config.get('acls'):
                config['acls'] = list()
            config['acls'].append(acls)

        if config not in render_config:
            render_config.append(utils.remove_empties(config))
        # delete the populated config
        del config

        return render_config
