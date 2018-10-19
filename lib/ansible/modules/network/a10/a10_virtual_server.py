#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Mischa Peters <mpeters@a10networks.com>,
#           Eric Chou <ericc@a10networks.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: a10_virtual_server
version_added: 1.8
short_description: Manage A10 Networks AX/SoftAX/Thunder/vThunder devices' virtual servers.
description:
    - Manage SLB (Server Load Balancing) virtual server objects on A10 Networks devices via aXAPIv2.
author: "Eric Chou (@ericchou) 2016, Mischa Peters (@mischapeters) 2014"
notes:
    - Requires A10 Networks aXAPI 2.1.
extends_documentation_fragment:
  - a10
  - url
options:
  state:
    description:
      - If the specified virtual server should exist.
    choices: ['present', 'absent']
    default: present
  partition:
    version_added: "2.3"
    description:
      - set active-partition
  virtual_server:
    description:
      - The SLB (Server Load Balancing) virtual server name.
    required: true
    aliases: ['vip', 'virtual']
  virtual_server_ip:
    description:
      - The SLB virtual server IPv4 address.
    aliases: ['ip', 'address']
  virtual_server_status:
    description:
      - The SLB virtual server status, such as enabled or disabled.
    default: enable
    aliases: ['status']
    choices: ['enabled', 'disabled']
  virtual_server_ports:
    description:
      - A list of ports to create for the virtual server. Each list item should be a
        dictionary which specifies the C(port:) and C(type:), but can also optionally
        specify the C(service_group:) as well as the C(status:). See the examples
        below for details. This parameter is required when C(state) is C(present).
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled devices using self-signed certificates.
    type: bool
    default: 'yes'

'''


EXAMPLES = '''
# Create a new virtual server
- a10_virtual_server:
    host: a10.mydomain.com
    username: myadmin
    password: mypassword
    partition: mypartition
    virtual_server: vserver1
    virtual_server_ip: 1.1.1.1
    virtual_server_ports:
      - port: 80
        protocol: TCP
        service_group: sg-80-tcp
      - port: 443
        protocol: HTTPS
        service_group: sg-443-https
      - port: 8080
        protocol: http
        status: disabled

'''

RETURN = '''
content:
  description: the full info regarding the slb_virtual
  returned: success
  type: string
  sample: "mynewvirtualserver"
'''
import json

from ansible.module_utils.network.a10.a10 import (axapi_call, a10_argument_spec, axapi_authenticate, axapi_failure,
                                                  axapi_enabled_disabled, axapi_get_vport_protocol, AXAPI_VPORT_PROTOCOLS)
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import url_argument_spec


VALID_PORT_FIELDS = ['port', 'protocol', 'service_group', 'status']


def validate_ports(module, ports):
    for item in ports:
        for key in item:
            if key not in VALID_PORT_FIELDS:
                module.fail_json(msg="invalid port field (%s), must be one of: %s" % (key, ','.join(VALID_PORT_FIELDS)))

        # validate the port number is present and an integer
        if 'port' in item:
            try:
                item['port'] = int(item['port'])
            except:
                module.fail_json(msg="port definitions must be integers")
        else:
            module.fail_json(msg="port definitions must define the port field")

        # validate the port protocol is present, and convert it to
        # the internal API integer value (and validate it)
        if 'protocol' in item:
            protocol = axapi_get_vport_protocol(item['protocol'])
            if not protocol:
                module.fail_json(msg="invalid port protocol, must be one of: %s" % ','.join(AXAPI_VPORT_PROTOCOLS))
            else:
                item['protocol'] = protocol
        else:
            module.fail_json(msg="port definitions must define the port protocol (%s)" % ','.join(AXAPI_VPORT_PROTOCOLS))

        # convert the status to the internal API integer value
        if 'status' in item:
            item['status'] = axapi_enabled_disabled(item['status'])
        else:
            item['status'] = 1

        # ensure the service_group field is at least present
        if 'service_group' not in item:
            item['service_group'] = ''


def main():
    argument_spec = a10_argument_spec()
    argument_spec.update(url_argument_spec())
    argument_spec.update(
        dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            virtual_server=dict(type='str', aliases=['vip', 'virtual'], required=True),
            virtual_server_ip=dict(type='str', aliases=['ip', 'address'], required=True),
            virtual_server_status=dict(type='str', default='enabled', aliases=['status'], choices=['enabled', 'disabled']),
            virtual_server_ports=dict(type='list', required=True),
            partition=dict(type='str', default=[]),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    host = module.params['host']
    username = module.params['username']
    password = module.params['password']
    partition = module.params['partition']
    state = module.params['state']
    write_config = module.params['write_config']
    slb_virtual = module.params['virtual_server']
    slb_virtual_ip = module.params['virtual_server_ip']
    slb_virtual_status = module.params['virtual_server_status']
    slb_virtual_ports = module.params['virtual_server_ports']

    if slb_virtual is None:
        module.fail_json(msg='virtual_server is required')

    validate_ports(module, slb_virtual_ports)

    axapi_base_url = 'https://%s/services/rest/V2.1/?format=json' % host
    session_url = axapi_authenticate(module, axapi_base_url, username, password)

    axapi_call(module, session_url + '&method=system.partition.active', json.dumps({'name': partition}))
    slb_virtual_data = axapi_call(module, session_url + '&method=slb.virtual_server.search', json.dumps({'name': slb_virtual}))
    slb_virtual_exists = not axapi_failure(slb_virtual_data)

    changed = False
    if state == 'present':
        json_post = {
            'virtual_server': {
                'name': slb_virtual,
                'address': slb_virtual_ip,
                'status': axapi_enabled_disabled(slb_virtual_status),
                'vport_list': slb_virtual_ports,
            }
        }

        # before creating/updating we need to validate that any
        # service groups defined in the ports list exist since
        # since the API will still create port definitions for
        # them while indicating a failure occurred
        checked_service_groups = []
        for port in slb_virtual_ports:
            if 'service_group' in port and port['service_group'] not in checked_service_groups:
                # skip blank service group entries
                if port['service_group'] == '':
                    continue
                result = axapi_call(module, session_url + '&method=slb.service_group.search', json.dumps({'name': port['service_group']}))
                if axapi_failure(result):
                    module.fail_json(msg="the service group %s specified in the ports list does not exist" % port['service_group'])
                checked_service_groups.append(port['service_group'])

        if not slb_virtual_exists:
            result = axapi_call(module, session_url + '&method=slb.virtual_server.create', json.dumps(json_post))
            if axapi_failure(result):
                module.fail_json(msg="failed to create the virtual server: %s" % result['response']['err']['msg'])
            changed = True
        else:
            def needs_update(src_ports, dst_ports):
                '''
                Checks to determine if the port definitions of the src_ports
                array are in or different from those in dst_ports. If there is
                a difference, this function returns true, otherwise false.
                '''
                for src_port in src_ports:
                    found = False
                    different = False
                    for dst_port in dst_ports:
                        if src_port['port'] == dst_port['port']:
                            found = True
                            for valid_field in VALID_PORT_FIELDS:
                                if src_port[valid_field] != dst_port[valid_field]:
                                    different = True
                                    break
                            if found or different:
                                break
                    if not found or different:
                        return True
                # every port from the src exists in the dst, and none of them were different
                return False

            defined_ports = slb_virtual_data.get('virtual_server', {}).get('vport_list', [])

            # we check for a needed update both ways, in case ports
            # are missing from either the ones specified by the user
            # or from those on the device
            if needs_update(defined_ports, slb_virtual_ports) or needs_update(slb_virtual_ports, defined_ports):
                result = axapi_call(module, session_url + '&method=slb.virtual_server.update', json.dumps(json_post))
                if axapi_failure(result):
                    module.fail_json(msg="failed to create the virtual server: %s" % result['response']['err']['msg'])
                changed = True

        # if we changed things, get the full info regarding
        # the service group for the return data below
        if changed:
            result = axapi_call(module, session_url + '&method=slb.virtual_server.search', json.dumps({'name': slb_virtual}))
        else:
            result = slb_virtual_data
    elif state == 'absent':
        if slb_virtual_exists:
            result = axapi_call(module, session_url + '&method=slb.virtual_server.delete', json.dumps({'name': slb_virtual}))
            changed = True
        else:
            result = dict(msg="the virtual server was not present")

    # if the config has changed, save the config unless otherwise requested
    if changed and write_config:
        write_result = axapi_call(module, session_url + '&method=system.action.write_memory')
        if axapi_failure(write_result):
            module.fail_json(msg="failed to save the configuration: %s" % write_result['response']['err']['msg'])

    # log out of the session nicely and exit
    axapi_call(module, session_url + '&method=session.close')
    module.exit_json(changed=changed, content=result)


if __name__ == '__main__':
    main()
