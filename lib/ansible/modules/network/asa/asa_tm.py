#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function
import re
import sys
from ipaddress import IPv4Network
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: asa_tm
version_added: "2.8"
author: "Federico Olivieri (@Federico87)"
short_description: Manage access-lists on a Cisco ASA
description:
  - This module allows you to work with access-lists on a Cisco ASA device.
extends_documentation_fragment: asa
options:
  source:
    description:
      - Source ip address
  destination:
    description:
      - Destination ip address
  dst_port:
    description:
      - Port
  protocol:
    description:
      - Protocol
    choices: ['udp', 'tcp', 'ip']
  interface:
    description:
      - Inbound interface where ACL is applied
  log:
    description:
      - Enable ACL logs
    type: bool
    default: False
  remark:
    description:
      - ACL remark
  id:
    description:
      - Unique ACL rule ID
"""

EXAMPLES = """
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
---
acl_tm:
    source: 10.0.0.0/8
    destination: 8.8.8.8/32
    dst_port: domain
    protocol: udp
    interface: outside
    remark: allow_google_dns
    log: False
    id: TICKET_#666
    state: present
"""

RETURN = """
commands:
  description: command sent to the device
  returned: always
  type: list
  sample: [
    "object-group network N-10.0.0.0-24",
    "network-object 10.0.0.0 255.255.255.0",
    "object-group network SG-TICKET_#666",
    "group-object N-10.0.0.0-24",
    "object-group network H-8.8.8.8-32",
    "network-object host 8.8.8.8",
    "object-group network DG-TICKET_#666",
    "group-object N-8.8.8.8-32",
    "access-list outside remark allow_google_dns",
    "access-list outside  permit udp  object-group SG-TICKET_#666 object-group DG-TICKET_#666  eq domain"
    ]
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.asa.asa import asa_argument_spec, check_args
from ansible.module_utils.network.asa.asa import get_config, load_config, run_commands
from ansible.module_utils.network.common.config import NetworkConfig, dumps


class Parser():
    '''Regex class for outputs parsing'''

    def __init__(self, config):
        '''Parser __init__ method'''
        self.config = config

    def parse_obj(self):
        '''object-group network N-10.0.0.0-24 --> str(10.0.0.0-24)'''
        match = re.search(r'(?:network\s)(?:N?H?.)(\d+\.\d+\.\d+\.\d+.\d+)', self.config, re.M)
        if match:
            object_grp = match.group(1)
            return str(object_grp.replace('-','/'))

    def parse_port(self):
        '''eq domain --> list(domain)'''
        match = re.findall(r'(?:eq\s)(\w+)', self.config, re.M)
        if match:
            return str(match[0])

    def parse_prot(self):
        '''access-list outside extended permit udp --> str(udp)'''
        match = re.search(r'(?:permit\s|deny\s)(\w+)', self.config, re.M)
        if match:
            return str(match.group(1))

    def parse_interf(self):
        '''access-list outside extended --> str(outside)'''
        match = re.search(r'(?:access-list\s)(\w+)', self.config, re.M)
        if match:
            return str(match.group(1))

    def parse_log(self):
        '''eq domain log --> str(log)'''
        match = re.search(r'(log)', self.config, re.M)
        if match:
            return str(match.group(1))

    def parse_remark(self):
        '''access-list outside remark NEE-TEST-666 --> str(NEE-TEST-666)'''
        match = re.search(r'(?:remark\s)(\S+)', self.config, re.M)
        if match:
            return str(match.group(1))

    def parse_ip_cidr(self):
        '''group-object N-10.0.0.0-24 --> list(10.0.0.0-24)'''
        ip_list = list()
        match = re.findall(r'(\d+\.\d+\.\d+\.\d+.\d+)', self.config, re.M)
        if match:
            for i in match:
                ip_list.append(i.replace('-','/'))
            return ip_list

    def parse_grp_obj(self):
        '''group-object N-10.0.0.0-24 --> list(N-10.0.0.0-24)'''
        grp_list = list()
        match = re.findall(r'(?:group-object\s)(\S+)', self.config, re.M)
        if match:
            for i in match:
                grp_list.append(i)
            return grp_list


def map_config_to_obj(module):

    obj = list()
    obj_dict = dict()

    id_module = module.params['id']             # str(NE-666)

    src_module = module.params['source']        # str(8.8.8.8/32)
    src_ip = src_module.split('/')[0]           # str(8.8.8.8)
    src_mask = int(src_module.split('/')[1])    # int(32)

    dst_module = module.params['destination']   # str(10.0.0.0/8)
    dst_ip = dst_module.split('/')[0]           # str(10.0.0.0)
    dst_mask = int(dst_module.split('/')[1])    # int(8)


    config = get_config(module, flags=['access-list | include {}'.format(id_module)])
    run_remark = get_config(module, flags=['| include {}'.format(module.params['remark'])])
    sg_obj_raw = get_config(module, flags=['object-group id SG-{}'.format(id_module)])
    dg_obj_raw = get_config(module, flags=['object-group id DG-{}'.format(id_module)])

    if src_mask == 32:
        src_grp_object = get_config(module, flags=['object-group id H-{}-32'.format(src_ip)])
        src_config_obj = get_config(module, flags=['| include H-{}-32'.format(src_ip)])
        src_host_obj_use = Parser(src_config_obj).parse_grp_obj()

        if src_host_obj_use:
            if len(src_host_obj_use) == len(set(src_host_obj_use)):
                obj_dict['src_hst_obj_run'] = True     # Can be removed
            elif len(src_host_obj_use) != len(set(src_host_obj_use)):
                obj_dict['src_hst_obj_run'] = False    # CANNOT be removed
                obj_dict['src_hst_obj_run_ip'] = src_host_obj_use

    elif 0 <= src_mask <= 31:
        src_grp_object = get_config(module, flags=['object-group id N-{}-{}'.format(src_ip, src_mask)])
        src_config_obj = get_config(module, flags=['| include N-{}-{}'.format(src_ip, src_mask)])
        src_net_obj_use = Parser(src_config_obj).parse_grp_obj()

        if src_net_obj_use:
            if len(src_net_obj_use) == len(set(src_net_obj_use)):
                obj_dict['src_net_obj_run'] = True
            elif len(src_net_obj_use) != len(set(src_net_obj_use)):
                obj_dict['src_net_obj_run'] = False
                obj_dict['src_net_obj_run_ip'] = src_net_obj_use

    else:
        sys.exit('CIDR must be between 0 and 32')


    if dst_mask == 32:
        dst_grp_object = get_config(module, flags=['object-group id H-{}-32'.format(dst_ip)])
        dst_config_obj = get_config(module, flags=['| include H-{}-32'.format(dst_ip)])
        dst_host_obj_use = Parser(dst_config_obj).parse_grp_obj()

        if dst_host_obj_use:
            if len(dst_host_obj_use) == len(set(dst_host_obj_use)):
                obj_dict['dst_host_obj_run'] = True
            elif len(dst_host_obj_use) != len(set(dst_host_obj_use)):
                obj_dict['dst_host_obj_run'] = False
                obj_dict['dst_host_obj_run_ip'] = dst_host_obj_use

    elif 0 <= dst_mask <= 31:
        dst_grp_object = get_config(module, flags=['object-group id N-{}-{}'.format(dst_ip, dst_mask)])
        dst_config_obj = get_config(module, flags=['| include N-{}-{}'.format(dst_ip, dst_mask)])
        dst_net_obj_use = Parser(dst_config_obj).parse_grp_obj()

        if dst_net_obj_use:
            if len(dst_net_obj_use) == len(set(dst_net_obj_use)):
                obj_dict['dst_net_obj_run'] = True
            elif len(dst_net_obj_use) != len(set(dst_net_obj_use)):
                obj_dict['dst_net_obj_run'] = False
                obj_dict['dst_net_obj_run_ip'] = dst_net_obj_use
    else:
        sys.exit('CIDR must be between 0 and 32')


    obj_dict['sg_obj'] = Parser(sg_obj_raw).parse_ip_cidr()
    obj_dict['dg_obj'] = Parser(dg_obj_raw).parse_ip_cidr()
    obj_dict['sg_obj_raw'] = sg_obj_raw
    obj_dict['dg_obj_raw'] = dg_obj_raw


    if src_grp_object:
        source = Parser(src_grp_object).parse_obj()
        obj_dict['source'] = source

    if dst_grp_object:
        destination = Parser(dst_grp_object).parse_obj()
        obj_dict['destination'] = destination

    if run_remark:
        remark = Parser(run_remark).parse_remark()
        obj_dict['remark'] = remark

    for i in config.splitlines():
        dst_port = Parser(i).parse_port()
        obj_dict['dst_port'] = dst_port

        protocol = Parser(i).parse_prot()
        obj_dict['protocol'] = protocol

        interface = Parser(i).parse_interf()
        obj_dict['interface'] = interface

        log = Parser(i).parse_log()
        obj_dict['log'] = log

        if id_module in i:
            obj_dict['id'] = id_module



    obj.append(obj_dict)

    return obj


def map_params_to_obj(module):

    obj = list()

    obj.append({
        'source': module.params['source'],
        'destination': module.params['destination'],
        'dst_port': module.params['dst_port'],
        'protocol': module.params['protocol'],
        'interface': module.params['interface'],
        'log': module.params['log'],
        'remark': module.params['remark'],
        'id': module.params['id'],
        'state': module.params['state']
    })

    return obj


def map_obj_to_commands(want, have, module):

    commands = list()
    acl_line = []
    
    source_have = have[0].get('source')
    destination_have = have[0].get('destination')
    dst_port_have = have[0].get('dst_port')
    protocol_have = have[0].get('protocol')
    interface_have = have[0].get('interface')
    log_have = have[0].get('log')
    remark_have = have[0].get('remark')
    id_have = have[0].get('id')
    sg_have = have[0].get('sg_obj')
    dg_have = have[0].get('dg_obj')
    sg_obj_raw = have[0].get('sg_obj_raw')
    dg_obj_raw = have[0].get('dg_obj_raw')
    src_hst_obj_run = have[0].get('src_hst_obj_run')
    src_net_obj_run = have[0].get('src_net_obj_run')
    dst_host_obj_run = have[0].get('dst_host_obj_run')
    dst_net_obj_run = have[0].get('dst_net_obj_run')
    src_hst_obj_run_ip = have[0].get('src_hst_obj_run_ip')
    src_net_obj_run_ip = have[0].get('src_net_obj_run_ip')
    dst_host_obj_run_ip = have[0].get('dst_host_obj_run_ip')
    dst_net_obj_run_ip = have[0].get('dst_net_obj_run_ip')

    for w in want:
        source_cidr = w['source']
        dest_cidr = w['destination']
        source = w['source'].split('/')[0]
        source_mask = int(w['source'].split('/')[1])
        destination = w['destination'].split('/')[0]
        destination_mask = int(w['destination'].split('/')[1])
        dst_port = w['dst_port']
        protocol = w['protocol']
        interface = w['interface']
        log = w['log']
        remark = w['remark']
        id = w['id']
        state = w['state']

        if state == 'absent':

            if id == id_have:

                if remark_have and remark == remark_have:
                    commands.append('no access-list {} remark {}'.format(interface, remark))
                if interface_have and interface in interface_have:
                    acl_line.append('no access-list {}'.format(interface))
                if protocol_have and protocol in protocol_have:
                    acl_line.append(' permit {} object-group SG-{} object-group DG-{}'.format(protocol, id, id))
                if dst_port_have and dst_port in dst_port_have:
                    acl_line.append(' eq {}'.format(dst_port))
                if log_have and log in log_have:
                    acl_line.append(' log'.format(log))

                acl = ' '.join(acl_line)
                commands.append(acl)

                if dg_have and 'does not exist' not in dg_obj_raw:

                    if dst_host_obj_run == True:
                        commands.append(dg_obj_raw.replace('object-group network', 'no object-group network').replace('group-object', 'no object-group network'))

                    elif dst_host_obj_run == False:
                        for i in set(dst_host_obj_run_ip):
                            edited = dg_obj_raw.replace('group-object {}'.format(i), '')
                        commands.append(edited.replace('object-group network', 'no object-group network').replace('group-object', 'no object-group network'))


                    if dst_net_obj_run == True:
                        commands.append(dg_obj_raw.replace('object-group network', 'no object-group network').replace('group-object', 'no object-group network'))

                    elif dst_net_obj_run == False:
                        for i in set(dst_net_obj_run_ip):
                            edited = dg_obj_raw.replace('group-object {}'.format(i), '')
                        commands.append(edited.replace('object-group network', 'no object-group network').replace('group-object', 'no object-group network'))


                if sg_have and 'does not exist' not in sg_obj_raw:

                    if src_hst_obj_run == True:
                        commands.append(sg_obj_raw.replace('object-group network', 'no object-group network').replace('group-object', 'no object-group network'))

                    elif src_hst_obj_run == False:
                        for i in set(src_hst_obj_run_ip):
                            edited = sg_obj_raw.replace('group-object {}'.format(i), '')
                        commands.append(edited.replace('object-group network', 'no object-group network').replace('group-object', 'no object-group network'))


                    if src_net_obj_run == True:
                        commands.append(sg_obj_raw.replace('object-group network', 'no object-group network').replace('group-object', 'no object-group network'))

                    elif src_net_obj_run == False:
                        for i in set(src_net_obj_run_ip):
                            edited = sg_obj_raw.replace('group-object {}'.format(i), '')
                        commands.append(edited.replace('object-group network', 'no object-group network').replace('group-object', 'no object-group network'))

        elif state == 'present':

            if id != id_have:

                if source != source_have and source_have is None:

                    if source_mask == 32:
                        commands.append('object-group network H-{}-32'.format(source))
                        commands.append('network-object host {}'.format(source))

                    elif 0 <= source_mask <= 31:
                        commands.append('object-group network N-{}-{}'.format(source, source_mask))
                        commands.append('network-object {} {}'.format(source, IPv4Network(unicode(source_cidr)).netmask))
                    else:
                        sys.exit('CIDR must be between 0 and 32')

                if source_mask == 32:
                    if sg_have is None or source_cidr not in sg_have:
                        commands.append('object-group network SG-{}'.format(id))
                        commands.append('group-object H-{}-32'.format(source))

                elif 0 <= source_mask <= 31:
                    if sg_have is None or source_cidr not in sg_have:
                        commands.append('object-group network SG-{}'.format(id))
                        commands.append('group-object N-{}-{}'.format(source, source_mask))

                else:
                    sys.exit('CIDR must be between 0 and 32')


                if destination != destination_have and destination_have is None:

                    if destination_mask == 32:
                        commands.append('object-group network H-{}-32'.format(destination))
                        commands.append('network-object host {}'.format(destination))

                    elif 0 <= destination_mask <= 31:
                        commands.append('object-group network N-{}-{}'.format(destination, destination_mask))
                        commands.append('network-object {} {}'.format(destination, IPv4Network(unicode(dest_cidr)).netmask))

                    else:
                        sys.exit('CIDR must be between 0 and 32')

                if destination_mask == 32:
                    if dg_have is None or dest_cidr not in dg_have:
                        commands.append('object-group network DG-{}'.format(id))
                        commands.append('group-object H-{}-32'.format(destination))

                elif 0 <= destination_mask <= 31:
                    if dg_have is None or dest_cidr not in dg_have:
                        commands.append('object-group network DG-{}'.format(id))
                        commands.append('group-object N-{}-{}'.format(destination, destination_mask))

                else:
                    sys.exit('CIDR must be between 0 and 32')


                if remark and remark != remark_have:
                    if interface and interface != interface_have:
                        commands.append('access-list {} remark {}'.format(interface, remark))
                if interface and interface != interface_have:
                    acl_line.append('access-list {}'.format(interface))
                if protocol and protocol != protocol_have:
                    acl_line.append(' permit {}'.format(protocol))
                if id and id != id_have:
                    acl_line.append(' object-group SG-{} object-group DG-{}'.format(id, id))
                if dst_port and dst_port != dst_port_have:
                    acl_line.append(' eq {}'.format(dst_port))
                if log and log_have and log != log_have:
                    acl_line.append(' log'.format(log))

                acl = ' '.join(acl_line)
                commands.append(acl)

    if "" in commands:
        return commands.remove("")
    else:
        return commands

def main():

    argument_spec = dict(
        source=dict(),
        destination=dict(),
        dst_port=dict(),
        protocol=dict(choices=['udp', 'tcp', 'ip']),
        interface=dict(),
        log=dict(type='bool', choices=[True, False], default=False),
        remark=dict(),
        id=dict(),
        state=dict(choices=['absent', 'present'], default='present')
    )

    argument_spec.update(asa_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = {'changed': False}

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands(want, have, module)

    result['commands'] = commands

    if commands:
        if not module.check_mode:
            load_config(module, commands)
        result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
