#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Dag Wieers (dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: cobbler_system
version_added: '2.7'
short_description: Manage system objects in Cobbler
description:
- Add, modify or remove systems in Cobbler
options:
  host:
    description:
    - The name or IP address of the Cobbler system.
    default: 127.0.0.1
  port:
    description:
    - Port number to be used for REST connection.
    - The default value depends on parameter C(use_ssl).
  username:
    description:
    - The username to log in to Cobbler.
    default: cobbler
  password:
    description:
    - The password to log in to Cobbler.
    required: yes
  use_ssl:
    description:
    - If C(no), an HTTP connection will be used instead of the default HTTPS connection.
    type: bool
    default: 'yes'
  validate_certs:
    description:
    - If C(no), SSL certificates will not be validated.
    - This should only set to C(no) when used on personally controlled sites using self-signed certificates.
    type: bool
    default: 'yes'
  name:
    description:
    - The system name to manage.
  properties:
    description:
    - A dictionary with system properties.
  interfaces:
    description:
    - A list of dictionaries containing interface options.
  sync:
    description:
    - Sync on changes.
    - Concurrently syncing Cobbler is bound to fail.
    type: bool
    default: no
  state:
    description:
    - Whether the system should be present, absent or a query is made.
    choices: [ absent, present, query ]
    default: present
author:
- Dag Wieers (@dagwieers)
notes:
- Concurrently syncing Cobbler is bound to fail with weird errors.
- On python 2.7.8 and older (i.e. on RHEL7) you may need to tweak the python behaviour to disable certificate validation.
  More information at L(Certificate verification in Python standard library HTTP clients,https://access.redhat.com/articles/2039753).
'''

EXAMPLES = r'''
- name: Ensure the system exists in Cobbler
  cobbler_system:
    host: cobbler01
    username: cobbler
    password: MySuperSecureP4sswOrd
    name: myhost
    properties:
      profile: CentOS6-x86_64
      name_servers: [ 2.3.4.5, 3.4.5.6 ]
      name_servers_search: foo.com, bar.com
    interfaces:
      eth0:
        macaddress: 00:01:02:03:04:05
        ipaddress: 1.2.3.4
  delegate_to: localhost

- name: Enable network boot in Cobbler
  cobbler_system:
    host: bdsol-aci-cobbler-01
    username: cobbler
    password: ins3965!
    name: bdsol-aci51-apic1.cisco.com
    properties:
      netboot_enabled: yes
    state: present
  delegate_to: localhost

- name: Query all systems in Cobbler
  cobbler_system:
    host: cobbler01
    username: cobbler
    password: MySuperSecureP4sswOrd
  register: cobbler_systems
  delegate_to: localhost

- name: Query a specific system in Cobbler
  cobbler_system:
    host: cobbler01
    username: cobbler
    password: MySuperSecureP4sswOrd
    name: '{{ inventory_hostname }}'
  register: cobbler_properties
  delegate_to: localhost

- name: Ensure the system does not exist in Cobbler
  cobbler_system:
    host: cobbler01
    username: cobbler
    password: MySuperSecureP4sswOrd
    name: myhost
  delegate_to: localhost
'''

RETURN = r'''
systems:
  description: List of systems
  returned: C(state=query) and C(name) is not provided
  type: list
system:
  description: (Resulting) information about the system we are working with
  returned: when C(name) is provided
  type: dict
'''

import copy
import datetime
import ssl

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.six.moves import xmlrpc_client
from ansible.module_utils._text import to_text

IFPROPS_MAPPING = dict(
    bondingopts='bonding_opts',
    bridgeopts='bridge_opts',
    connected_mode='connected_mode',
    cnames='cnames',
    dhcptag='dhcp_tag',
    dnsname='dns_name',
    ifgateway='if_gateway',
    interfacetype='interface_type',
    interfacemaster='interface_master',
    ipaddress='ip_address',
    ipv6address='ipv6_address',
    ipv6defaultgateway='ipv6_default_gateway',
    ipv6mtu='ipv6_mtu',
    ipv6prefix='ipv6_prefix',
    ipv6secondaries='ipv6_secondariesu',
    ipv6staticroutes='ipv6_static_routes',
    macaddress='mac_address',
    management='management',
    mtu='mtu',
    netmask='netmask',
    static='static',
    staticroutes='static_routes',
    virtbridge='virt_bridge',
)


def getsystem(conn, name, token):
    system = dict()
    if name:
        # system = conn.get_system(name, token)
        systems = conn.find_system(dict(name=name), token)
        if systems:
            system = systems[0]
    return system


def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', default='127.0.0.1'),
            port=dict(type='int'),
            username=dict(type='str', default='cobbler'),
            password=dict(type='str', no_log=True),
            use_ssl=dict(type='bool', default=True),
            validate_certs=dict(type='bool', default=True),
            name=dict(type='str'),
            interfaces=dict(type='dict'),
            properties=dict(type='dict'),
            sync=dict(type='bool', default=False),
            state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        ),
        supports_check_mode=True,
    )

    username = module.params['username']
    password = module.params['password']
    port = module.params['port']
    use_ssl = module.params['use_ssl']
    validate_certs = module.params['validate_certs']

    name = module.params['name']
    state = module.params['state']

    module.params['proto'] = 'https' if use_ssl else 'http'
    if not port:
        module.params['port'] = '443' if use_ssl else '80'

    result = dict(
        changed=False,
    )

    start = datetime.datetime.utcnow()

    ssl_context = None
    if not validate_certs:
        try:  # Python 2.7.9 and newer
            ssl_context = ssl.create_unverified_context()
        except AttributeError:  # Legacy Python that doesn't verify HTTPS certificates by default
            ssl._create_default_context = ssl._create_unverified_context
        else:  # Python 2.7.8 and older
            ssl._create_default_https_context = ssl._create_unverified_https_context

    url = '{proto}://{host}:{port}/cobbler_api'.format(**module.params)
    if ssl_context:
        conn = xmlrpc_client.ServerProxy(url, context=ssl_context)
    else:
        conn = xmlrpc_client.Server(url)

    try:
        token = conn.login(username, password)
    except xmlrpc_client.Fault as e:
        module.fail_json(msg="Failed to log in to Cobbler '{url}' as '{username}'. {error}".format(url=url, error=to_text(e), **module.params))
    except Exception as e:
        module.fail_json(msg="Connection to '{url}' failed. {error}".format(url=url, error=to_text(e), **module.params))

    system = getsystem(conn, name, token)
    # result['system'] = system

    if state == 'query':
        if name:
            result['system'] = system
        else:
            # Turn it into a dictionary of dictionaries
            # all_systems = conn.get_systems()
            # result['systems'] = { system['name']: system for system in all_systems }

            # Return a list of dictionaries
            result['systems'] = conn.get_systems()

    elif state == 'present':

        if system:
            # Update existing entry
            system_id = conn.get_system_handle(name, token)

            for key, value in iteritems(module.params['properties']):
                if key not in system:
                    module.warn("Property '{0}' is not a valid system property.".format(key))
                if system[key] != value:
                    try:
                        conn.modify_system(system_id, key, value, token)
                        result['changed'] = True
                    except Exception as e:
                        module.fail_json(msg="Unable to change '{0}' to '{1}'. {2}".format(key, value, e))

        else:
            # Create a new entry
            system_id = conn.new_system(token)
            conn.modify_system(system_id, 'name', name, token)
            result['changed'] = True

            if module.params['properties']:
                for key, value in iteritems(module.params['properties']):
                    try:
                        conn.modify_system(system_id, key, value, token)
                    except Exception as e:
                        module.fail_json(msg="Unable to change '{0}' to '{1}'. {2}".format(key, value, e))

        # Add interface properties
        interface_properties = dict()
        if module.params['interfaces']:
            for device, values in iteritems(module.params['interfaces']):
                for key, value in iteritems(values):
                    if key == 'name':
                        continue
                    if key not in IFPROPS_MAPPING:
                        module.warn("Property '{0}' is not a valid system property.".format(key))
                    if not system or system['interfaces'][device][IFPROPS_MAPPING[key]] != value:
                        result['changed'] = True
                    interface_properties['{0}-{1}'.format(key, device)] = value

            if result['changed'] is True:
                conn.modify_system(system_id, "modify_interface", interface_properties, token)

        # Only save when the entry was changed
        if not module.check_mode and result['changed']:
            conn.save_system(system_id, token)

    elif state == 'absent':

        if system:
            if not module.check_mode:
                conn.remove_system(name, token)
            result['changed'] = True

    if not module.check_mode and module.params['sync'] and result['changed']:
        try:
            conn.sync(token)
        except Exception as e:
            module.fail_json(msg="Failed to sync Cobbler. {0}".format(to_text(e)))

    if state in ('absent', 'present'):
        result['system'] = getsystem(conn, name, token)

        if module._diff:
            result['diff'] = dict(before=system, after=result['system'])

    elapsed = datetime.datetime.utcnow() - start
    module.exit_json(elapsed=elapsed.seconds, **result)


if __name__ == '__main__':
    main()
