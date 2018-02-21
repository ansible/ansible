#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: nios_nsgroup
short_description: Configure InfoBlox DNS nameserver groups
extends_documentation_fragment: nios
author:
    - Erich Birngruber (@ebirn)
version_added: "2.6"
description:
    - Adds and/or removes nameserver groups form Infoblox NIOS servers.
      This module manages NIOS C(nsgroup) objects using the Infoblox
      WAPI interface over REST.
requirements:
  - infoblox_client
options:
  name:
    description:
      - Specifies the name of the NIOS nameserver group to be managed.
    required: true
  grid_primary:
    description:
      - This list of hosts is to be used as primary servers in this nameserver group. They must be grid members.
        This option is required when setting I(use_external_primaries) to C(false).
  grid_secondaries:
    description:
     - Configures the list of grid member hosts that act as secondary nameservers.
       This option is required when setting I(use_external_primaries) to C(true). 
  is_grid_default:
    description:
      - If set to C(True) this nsgroup will become the default nameserver group for new zones.
    required: false
    default: false
  use_external_primary:
    description:
      - This flag controls whether the group is using an external primary nameserver.
        Note that modification of this field requires passing values for I(grid_secondaries) and I(external_primaries).
    required: false
    default: false
  external_primaries:
    description:
      - Configures a list of external nameservers (non-members of the grid).
        This option is required when setting I(use_external_primaries) to C(true).
    required: false
  external_secondaries:
    description:
      - Allows to provide a list of external secondary nameservers, that are not members of the grid.
  extattrs:
    description:
      - Allows for the configuration of Extensible Attributes on the
        instance of the object.  This argument accepts a set of key / value
        pairs for configuration.
    required: false
  comment:
    description:
      - Configures a text string comment to be associated with the instance
        of this object.  The provided text string will be configured on the
        object instance.
    required: false
  state:
    description:
      - Configures the intended state of the instance of the object on
        the NIOS server.  When this value is set to C(present), the object
        is configured on the device and when this value is set to C(absent)
        the value is removed (if necessary) from the device.
    choices: [present, absent]
    default: present
'''

EXAMPLES = '''
- name: create simple infoblox nameserver group
  nios_nsgroup:
    provider:
      username: admin
      password: password
      host: infoblox-test.example.com
      wapi_version: 2.1
    name: my-simple-group
    comment: "this is a simple nameserver group"
    grid_primary:
      - name: infoblox-test.example.com
  state: present
  connection: local

- name: create infoblox nameserver group with external primaries
  nios_nsgroup:
    provider:
      username: admin
      password: password
      host: infoblox-test.example.com
      wapi_version: 2.1
    name: my-example-group
    use_external_primary: true
    comment: "this is my example nameserver group"
    external_primaries: "{{ ext_nameservers }}"
    grid_secondaries:
      - name: infoblox-test.example.com
        lead: True
        preferred_primaries: "{{ ext_nameservers }}"
  state: present
  connection: local
'''

RETURN = ''' # '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.net_tools.nios.api import WapiModule


# from infoblox documentation
# Fields List
# Field         Type            Req     R/O     Base    Search
# comment               String          N       N       Y       : = ~
# extattrs              Extattr         N       N       N       ext
# external_primaries    [struct]        N       N       N       N/A
# external_secondaries  [struct]        N       N       N       N/A
# grid_primary          [struct]        N       N       N       N/A
# grid_secondaries      [struct]        N       N       N       N/A
# is_grid_default       Bool            N       N       N       N/A
# is_multimaster        Bool            N       Y       N       N/A
# name                  String          Y               N       Y       : = ~
# use_external_primary  Bool            N       N       N       N/A


def main():
    '''entrypoint for module execution.'''
    argument_spec = dict(
        provider=dict(required=True),
        state=dict(default='present', choices=['present', 'absent']),
    )

    # cleanup tsig fields
    def clean_tsig(ext):
        if 'tsig_key' in ext and not ext['tsig_key']:
            del ext['tsig_key']
        if 'tsig_key' not in ext and 'tsig_key_name' in ext and not ext['tsig_key_name']:
            del ext['tsig_key_name']
        if 'tsig_key' not in ext and 'tsig_key_alg' in ext:
            del ext['tsig_key_alg']

    def clean_grid_member(member):
        if member['preferred_primaries']:
            for ext in member['preferred_primaries']:
                clean_tsig(ext)
        if member['enable_preferred_primaries'] is False:
            del member['enable_preferred_primaries']
            del member['preferred_primaries']
        if member['lead'] is False:
            del member['lead']
        if member['grid_replicate'] is False:
            del member['grid_replicate']

    def ext_primaries_transform(module):
        if module.params['external_primaries']:
            for ext in module.params['external_primaries']:
                clean_tsig(ext)
        return module.params['external_primaries']

    def ext_secondaries_transform(module):
        if module.params['external_secondaries']:
            for ext in module.params['external_secondaries']:
                clean_tsig(ext)
        return module.params['external_secondaries']

    def grid_primary_preferred_transform(module):
        for member in module.params['grid_primary']:
            clean_grid_member(member)
        return module.params['grid_primary']

    def grid_secondaries_preferred_primaries_transform(module):
        for member in module.params['grid_secondaries']:
            clean_grid_member(member)
        return module.params['grid_secondaries']

    extserver_spec = dict(
        address=dict(type='str', required=True, ib_req=True),
        name=dict(type='str', required=True, ib_req=True),
        stealth=dict(type='bool', default=False),
        tsig_key=dict(type='str', default=''),
        tsig_key_alg=dict(type='str', choices=['HMAC-MD5', 'HMAC-SHA256'], default='HMAC-MD5'),
        tsig_key_name=dict(type='str', default='', )
    )

    memberserver_spec = dict(
        enable_preferred_primaries=dict(type='bool', default=False),
        grid_replicate=dict(type='bool', default=False),
        lead=dict(type='bool', default=False),
        name=dict(type='str', required=True, ib_req=True),
        preferred_primaries=dict(type='list', elements='dict', options=extserver_spec, default=[]),
        stealth=dict(type='bool', default=False),
    )

    ib_spec = dict(
        name=dict(type='str', required=True, ib_req=True),
        grid_primary=dict(type='list', elements='dict', options=memberserver_spec,
                          transform=grid_primary_preferred_transform),
        grid_secondaries=dict(type='list', elements='dict', options=memberserver_spec,
                              transform=grid_secondaries_preferred_primaries_transform, default=[]),
        external_primaries=dict(type='list', elements='dict', options=extserver_spec, transform=ext_primaries_transform,
                                default=[]),
        external_secondaries=dict(type='list', elements='dict', options=extserver_spec,
                                  transform=ext_secondaries_transform, default=[]),
        is_grid_default=dict(type='bool', default=False),
        use_external_primary=dict(type='bool', default=False),
        extattrs=dict(),
        comment=dict(type='str', default=''),
    )

    argument_spec.update(ib_spec)
    argument_spec.update(WapiModule.provider_spec)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    wapi = WapiModule(module)
    result = wapi.run('nsgroup', ib_spec)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
