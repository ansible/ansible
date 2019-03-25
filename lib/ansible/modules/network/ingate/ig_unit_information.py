#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ingate Systems AB
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.1'
}

DOCUMENTATION = '''
---
module: ig_unit_information
short_description: Get unit information from an Ingate SBC.
description:
  - Get unit information from an Ingate SBC.
version_added: 2.8
extends_documentation_fragment: ingate
author:
  - Ingate Systems AB (@ingatesystems)
'''

EXAMPLES = '''
- name: Get unit information
  ig_unit_information:
    client:
      version: v1
      scheme: http
      address: 192.168.1.1
      username: alice
      password: foobar
'''

RETURN = '''
unit-information:
  description: Information about the unit
  returned: success
  type: complex
  contains:
    installid:
      description: The installation identifier
      returned: success
      type: str
      sample: any
    interfaces:
      description: List of interface names
      returned: success
      type: str
      sample: eth0 eth1 eth2 eth3 eth4 eth5
    lang:
      description: The unit's language
      returned: success
      type: str
      sample: en
    lic_email:
      description: License email information
      returned: success
      type: str
      sample: example@example.com
    lic_mac:
      description: License MAC information
      returned: success
      type: str
      sample: any
    lic_name:
      description: License name information
      returned: success
      type: str
      sample: Example Inc
    macaddr:
      description: The MAC address of the first interface
      returned: success
      type: str
      sample: 52:54:00:4c:e2:07
    mode:
      description: Operational mode of the unit
      returned: success
      type: str
      sample: Siparator
    modules:
      description: Installed module licenses
      returned: success
      type: str
      sample: failover vpn sip qturn ems qos rsc voipsm
    patches:
      description: Installed patches on the unit
      returned: success
      type: list
      sample: []
    product:
      description: The product name
      returned: success
      type: str
      sample: Software SIParator/Firewall
    serial:
      description: The serial number of the unit
      returned: success
      type: str
      sample: IG-200-839-2008-0
    systemid:
      description: The system identifier of the unit
      returned: success
      type: str
      sample: IG-200-839-2008-0
    unitname:
      description: The name of the unit
      returned: success
      type: str
      sample: Testname
    version:
      description: Firmware version
      returned: success
      type: str
      sample: 6.2.0-beta2
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.network.ingate.common import (ingate_argument_spec,
                                                        ingate_create_client,
                                                        is_ingatesdk_installed)

try:
    from ingate import ingatesdk
except ImportError:
    pass


def make_request(module):
    # Create client and authenticate.
    api_client = ingate_create_client(**module.params)

    # Get unit information.
    response = api_client.unit_information()
    return response


def main():
    argument_spec = ingate_argument_spec()
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)

    is_ingatesdk_installed(module)

    result = dict(changed=False)
    try:
        response = make_request(module)
        result.update(response[0])
    except ingatesdk.SdkError as e:
        module.fail_json(msg=to_native(e))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
