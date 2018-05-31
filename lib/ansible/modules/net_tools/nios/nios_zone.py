#!/usr/bin/python
# Copyright (c) 2018 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: nios_zone
version_added: "2.5"
author: "Peter Sprygada (@privateip)"
short_description: Configure Infoblox NIOS DNS zones
description:
  - Adds and/or removes instances of DNS zone objects from
    Infoblox NIOS servers.  This module manages NIOS C(zone_auth) objects
    using the Infoblox WAPI interface over REST.
requirements:
  - infoblox_client
extends_documentation_fragment: nios
options:
  fqdn:
    description:
      - Specifies the qualified domain name to either add or remove from
        the NIOS instance based on the configured C(state) value.
    required: true
    aliases:
      - name
  view:
    description:
      - Configures the DNS view name for the configured resource.  The
        specified DNS zone must already exist on the running NIOS instance
        prior to configuring zones.
    required: true
    default: default
    aliases:
      - dns_view
  grid_primary:
    description:
      - Configures the grid primary servers for this zone.
    suboptions:
      name:
        description:
          - The name of the grid primary server
  grid_secondaries:
    description:
      - Configures the grid secondary servers for this zone.
    suboptions:
      name:
        description:
          - The name of the grid secondary server
  ns_group:
    version_added: "2.6"
    description:
      - Configures the name server group for this zone. Name server group is
        mutually exclusive with grid primary and grid secondaries.
  restart_if_needed:
    version_added: "2.6"
    description:
      - If set to true, causes the NIOS DNS service to restart and load the
        new zone configuration
    type: bool
  extattrs:
    description:
      - Allows for the configuration of Extensible Attributes on the
        instance of the object.  This argument accepts a set of key / value
        pairs for configuration.
  comment:
    description:
      - Configures a text string comment to be associated with the instance
        of this object.  The provided text string will be configured on the
        object instance.
  state:
    description:
      - Configures the intended state of the instance of the object on
        the NIOS server.  When this value is set to C(present), the object
        is configured on the device and when this value is set to C(absent)
        the value is removed (if necessary) from the device.
    default: present
    choices:
      - present
      - absent
'''

EXAMPLES = '''
- name: configure a zone on the system using grid primary and secondaries
  nios_zone:
    name: ansible.com
    grid_primary:
      - name: gridprimary.grid.com
    grid_secondaries:
      - name: gridsecondary1.grid.com
      - name: gridsecondary2.grid.com
    restart_if_needed: true
    state: present
    provider:
      host: "{{ inventory_hostname_short }}"
      username: admin
      password: admin
  connection: local

- name: configure a zone on the system using a name server group
  nios_zone:
    name: ansible.com
    ns_group: examplensg
    restart_if_needed: true
    state: present
    provider:
      host: "{{ inventory_hostname_short }}"
      username: admin
      password: admin
  connection: local
- name: update the comment and ext attributes for an existing zone
  nios_zone:
    name: ansible.com
    comment: this is an example comment
    extattrs:
      Site: west-dc
    state: present
    provider:
      host: "{{ inventory_hostname_short }}"
      username: admin
      password: admin
  connection: local
- name: remove the dns zone
  nios_zone:
    name: ansible.com
    state: absent
    provider:
      host: "{{ inventory_hostname_short }}"
      username: admin
      password: admin
  connection: local
'''

RETURN = ''' # '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.net_tools.nios.api import WapiModule
from ansible.module_utils.net_tools.nios.api import NIOS_ZONE


def main():
    ''' Main entry point for module execution
    '''
    grid_spec = dict(
        name=dict(required=True),
    )

    ib_spec = dict(
        fqdn=dict(required=True, aliases=['name'], ib_req=True, update=False),
        view=dict(default='default', aliases=['dns_view'], ib_req=True),

        grid_primary=dict(type='list', elements='dict', options=grid_spec),
        grid_secondaries=dict(type='list', elements='dict', options=grid_spec),
        ns_group=dict(),
        restart_if_needed=dict(type='bool'),

        extattrs=dict(type='dict'),
        comment=dict()
    )

    argument_spec = dict(
        provider=dict(required=True),
        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(ib_spec)
    argument_spec.update(WapiModule.provider_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           mutually_exclusive=[
                               ['ns_group', 'grid_primary'],
                               ['ns_group', 'grid_secondaries']
                           ])

    wapi = WapiModule(module)
    result = wapi.run(NIOS_ZONE, ib_spec)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
