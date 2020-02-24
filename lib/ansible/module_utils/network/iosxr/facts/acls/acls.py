#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The iosxr acls fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from copy import deepcopy

from collections import deque
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.iosxr.argspec.acls.acls import AclsArgs
from ansible.module_utils.network.iosxr.utils.utils import isipaddress

PROTOCOL_OPTIONS = {
    'tcp': (
        'ack',
        'fin',
        'psh',
        'rst',
        'syn',
        'urg',
        'established',
    ),
    'igmp': ('dvmrp', 'host_query', 'host_report', 'mtrace', 'mtrace_response',
             'pim', 'trace', 'v2_leave', 'v2_report', 'v3_report'),
    'icmp':
    ('administratively_prohibited', 'alternate_address', 'conversion_error',
     'dod_host_prohibited', 'dod_net_prohibited', 'echo', 'echo_reply',
     'general_parameter_problem', 'host_isolated',
     'host_precedence_unreachable', 'host_redirect', 'host_tos_redirect',
     'host_tos_unreachable', 'host_unknown', 'host_unreachable',
     'information_reply', 'information_request', 'mask_reply', 'mask_request',
     'mobile_redirect', 'net_redirect', 'net_tos_redirect',
     'net_tos_unreachable', 'net_unreachable', 'network_unknown',
     'no_room_for_option', 'option_missing', 'packet_too_big',
     'parameter_problem', 'port_unreachable', 'precedence_unreachable',
     'protocol_unreachable', 'reassembly_timeout', 'redirect',
     'router_advertisement', 'router_solicitation', 'source_quench',
     'source_route_failed', 'time_exceeded', 'timestamp_reply',
     'timestamp_request', 'traceroute', 'ttl_exceeded', 'unreachable'),
    'icmpv6':
    ('address_unreachable', 'administratively_prohibited',
     'beyond_scope_of_source_address', 'destination_unreachable', 'echo',
     'echo_reply', 'erroneous_header_field', 'group_membership_query',
     'group_membership_report', 'group_membership_termination',
     'host_unreachable', 'nd_na', 'nd_ns', 'neighbor_redirect',
     'no_route_to_destination', 'node_information_request_is_refused',
     'node_information_successful_reply', 'packet_too_big',
     'parameter_problem', 'port_unreachable', 'query_subject_is_IPv4address',
     'query_subject_is_IPv6address', 'query_subject_is_domainname',
     'reassembly_timeout', 'redirect', 'router_advertisement',
     'router_renumbering', 'router_solicitation', 'rr_command', 'rr_result',
     'rr_seqnum_reset', 'time_exceeded', 'ttl_exceeded', 'unknown_query_type',
     'unreachable', 'unrecognized_next_header', 'unrecognized_option',
     'whoareyou_reply', 'whoareyou_request')
}


class AclsFacts(object):
    """ The iosxr acls fact class
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

    def get_device_data(self, connection):
        return connection.get('show access-lists afi-all')

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for acls
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = self.get_device_data(connection)

        objs = []

        acl_lines = data.splitlines()

        # We iterate through the data and create a list of ACLs
        # where each ACL is a dictionary in the following format:
        # {'afi': 'ipv4', 'name': 'acl_1', 'aces': ['10 permit 172.16.0.0 0.0.255.255', '20 deny 192.168.34.0 0.0.0.255']}
        if acl_lines:
            acl, acls = {}, []
            for line in acl_lines:
                if line.startswith('ip'):
                    if acl:
                        acls.append(acl)
                    acl = {'aces': []}
                    acl['afi'], acl['name'] = line.split()[0], line.split()[2]
                else:
                    acl['aces'].append(line.strip())
            acls.append(acl)

            # Here we group the ACLs based on AFI
            # {
            #   'ipv6': [{'aces': ['10 permit ipv6 2000::/12 any'], 'name': 'acl_2'}],
            #   'ipv4': [{'aces': ['10 permit 172.16.0.0 0.0.255.255', '20 deny 192.168.34.0 0.0.0.255'], 'name': 'acl_1'},
            #            {'aces': ['20 deny 10.0.0.0/8 log'], 'name': 'acl_3'}]
            # }

            grouped_acls = {'ipv4': [], 'ipv6': []}
            for acl in acls:
                acl_copy = deepcopy(acl)
                del acl_copy['afi']
                grouped_acls[acl['afi']].append(acl_copy)

            # Now that we have the ACLs in a fairly structured format,
            # we pass it on to render_config to convert it to model spec
            for key, value in iteritems(grouped_acls):
                obj = self.render_config(self.generated_spec, value)
                if obj:
                    obj['afi'] = key
                    objs.append(obj)

        ansible_facts['ansible_network_resources'].pop('acls', None)
        facts = {}

        facts['acls'] = []
        params = utils.validate_config(self.argument_spec, {'config': objs})
        for cfg in params['config']:
            facts['acls'].append(utils.remove_empties(cfg))

        ansible_facts['ansible_network_resources'].update(facts)

        return ansible_facts

    def render_config(self, spec, conf):
        """
        Render config as dictionary structure and delete keys
        from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)
        config['acls'] = []

        for item in conf:
            acl = {'name': item['name']}
            aces = item.get('aces', [])
            if aces:
                acl['aces'] = []
                for ace in aces:
                    acl['aces'].append(self._render_ace(ace))
            config['acls'].append(acl)

        return utils.remove_empties(config)

    def _render_ace(self, ace):
        """
        Parses an Access Control Entry (ACE) and converts it
        into model spec

        :param ace: An ACE in device specific format
        :rtype: dictionary
        :returns: The ACE in structured format
        """

        def __parse_src_dest(rendered_ace, ace_queue, direction):
            """
            Parses the ACE queue and populates address, wildcard_bits,
            host or any keys in the source/destination dictionary of
            ace dictionary, i.e., `rendered_ace`.

            :param rendered_ace: The dictionary containing the ACE in structured format
            :param ace_queue: The ACE queue
            :param direction: Specifies whether to populate `source` or `destination`
                              dictionary
            """
            element = ace_queue.popleft()
            if element == 'host':
                rendered_ace[direction] = {'host': ace_queue.popleft()}

            elif element == 'any':
                rendered_ace[direction] = {'any': True}

            elif '/' in element:
                rendered_ace[direction] = {
                    'prefix': element
                }

            elif isipaddress(element):
                rendered_ace[direction] = {
                    'address': element,
                    'wildcard_bits': ace_queue.popleft()
                }

        def __parse_port_protocol(rendered_ace, ace_queue, direction):
            """
            Parses the ACE queue and populates `port_protocol` dictionary in the
            ACE dictionary, i.e., `rendered_ace`.

            :param rendered_ace: The dictionary containing the ACE in structured format
            :param ace_queue: The ACE queue
            :param direction: Specifies whether to populate `source` or `destination`
                              dictionary
            """
            if len(ace_queue) > 0 and ace_queue[0] in ('eq', 'gt', 'lt', 'neq',
                                                       'range'):
                element = ace_queue.popleft()
                port_protocol = {}

                if element == 'range':
                    port_protocol['range'] = {
                        'start': ace_queue.popleft(),
                        'end': ace_queue.popleft()
                    }
                else:
                    port_protocol[element] = ace_queue.popleft()

                rendered_ace[direction]['port_protocol'] = port_protocol

        def __parse_protocol_options(rendered_ace, ace_queue, protocol):
            """
            Parses the ACE queue and populates protocol specific options
            of the required dictionary and updates the ACE dictionary, i.e.,
            `rendered_ace`.

            :param rendered_ace: The dictionary containing the ACE in structured format
            :param ace_queue: The ACE queue
            :param protocol: Specifies the protocol that will be populated under
                             `protocol_options` dictionary
            """
            if len(ace_queue) > 0:
                protocol_options = {protocol: {}}

                for match_bit in PROTOCOL_OPTIONS.get(protocol, ()):
                    if match_bit.replace('_', '-') in ace_queue:
                        protocol_options[protocol][match_bit] = True
                        ace_queue.remove(match_bit.replace('_', '-'))

                rendered_ace['protocol_options'] = protocol_options

        def __parse_match_options(rendered_ace, ace_queue):
            """
            Parses the ACE queue and populates remaining options in the ACE dictionary,
            i.e., `rendered_ace`

            :param rendered_ace: The dictionary containing the ACE in structured format
            :param ace_queue: The ACE queue
            """
            if len(ace_queue) > 0:
                # We deepcopy the actual queue and iterate through the
                # copied queue. However, we pop off the elements from
                # the actual queue. Then, in every pass we update the copied
                # queue with the current state of the original queue.
                # This is done because a queue cannot be mutated during iteration.
                copy_ace_queue = deepcopy(ace_queue)

                for element in copy_ace_queue:
                    if element == 'precedence':
                        ace_queue.popleft()
                        rendered_ace['precedence'] = ace_queue.popleft()

                    elif element == 'dscp':
                        ace_queue.popleft()
                        dscp = {}
                        operation = ace_queue.popleft()

                        if operation in ('eq', 'gt', 'neq', 'lt', 'range'):
                            if operation == 'range':
                                dscp['range'] = {
                                    'start': ace_queue.popleft(),
                                    'end': ace_queue.popleft()
                                }
                            else:
                                dscp[operation] = ace_queue.popleft()
                        else:
                            # `dscp` can be followed by either the dscp value itself or
                            # the same thing can be represented using "dscp eq <dscp_value>".
                            # In both cases, it would show up as {'dscp': {'eq': "dscp_value"}}.
                            dscp['eq'] = operation

                        rendered_ace['dscp'] = dscp

                    elif element in ('packet-length', 'ttl'):
                        ace_queue.popleft()
                        element_dict = {}
                        operation = ace_queue.popleft()

                        if operation == 'range':
                            element_dict['range'] = {
                                'start': ace_queue.popleft(),
                                'end': ace_queue.popleft()
                            }
                        else:
                            element_dict[operation] = ace_queue.popleft()

                        rendered_ace[element.replace('-', '_')] = element_dict

                    elif element in ('log', 'log-input', 'fragments',
                                     'icmp-off', 'capture', 'destopts',
                                     'authen', 'routing', 'hop-by-hop'):
                        rendered_ace[element.replace('-', '_')] = True
                        ace_queue.remove(element)

                    copy_ace_queue = deepcopy(ace_queue)

        rendered_ace = {}
        split_ace = ace.split()

        # Create a queue with each word in the ace
        # We parse each element and pop it off the queue
        ace_queue = deque(split_ace)

        # An ACE will always have a sequence number, even if
        # it is not explicitly provided while configuring
        sequence = int(ace_queue.popleft())
        rendered_ace['sequence'] = sequence
        operation = ace_queue.popleft()

        if operation == 'remark':
            rendered_ace['remark'] = ' '.join(split_ace[2:])

        else:
            rendered_ace['grant'] = operation

            # If the entry is a non-remark entry, the third element
            # will always be the protocol specified. By default, it's
            # the AFI.
            rendered_ace['protocol'] = ace_queue.popleft()

            # Populate source dictionary
            __parse_src_dest(rendered_ace, ace_queue, direction='source')
            # Populate port_protocol key in source dictionary
            __parse_port_protocol(rendered_ace, ace_queue, direction='source')
            # Populate destination dictionary
            __parse_src_dest(rendered_ace, ace_queue, direction='destination')
            # Populate port_protocol key in destination dictionary
            __parse_port_protocol(rendered_ace,
                                  ace_queue,
                                  direction='destination')
            # Populate protocol_options dictionary
            __parse_protocol_options(rendered_ace,
                                     ace_queue,
                                     protocol=rendered_ace['protocol'])
            # Populate remaining match options' dictionaries
            __parse_match_options(rendered_ace, ace_queue)

            # At this stage the queue should be empty
            # If the queue is not empty, it means that
            # we haven't been able to parse the entire ACE
            # In this case, we add the whole unprocessed ACE
            # to a key called `line` and send it back
            if len(ace_queue) > 0:
                rendered_ace = {
                    'sequence': sequence,
                    'line': ' '.join(split_ace[1:])
                }

        return utils.remove_empties(rendered_ace)
