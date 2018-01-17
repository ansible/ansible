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
module: aci_firmware_source
short_description: Manage firmware image sources on Cisco ACI fabrics (firmware:OSource)
description:
- Manage firmware image sources on Cisco ACI fabrics.
- More information from the internal APIC class I(firmware:OSource) at
  U(https://developer.cisco.com/docs/apic-mim-ref/).
author:
- Dag Wieers (@dagwieers)
version_added: '2.5'
options:
  source:
    description:
    - The identifying name for the outside source of images, such as an HTTP or SCP server.
    required: yes
    aliases: [ name, source_name ]
  polling_interval:
    description:
    - Polling interval in minutes.
  protocol:
    description:
    - The Firmware download protocol.
    choices: [ http, local, scp, usbkey ]
    default: scp
    aliases: [ proto ]
  url:
    description:
      The firmware URL for the image(s) on the source.
  url_password:
    description:
      The Firmware password or key string.
  url_username:
    description:
      The username for the source.
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
#
'''

RETURN = r'''
#
'''


from ansible.module_utils.network.aci.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec()
    argument_spec.update(
        source=dict(type='str', aliases=['name', 'source_name']),  # Not required for querying all objects
        polling_interval=dict(type='int'),
        protocol=dict(type='str', default='scp', choices=['http', 'local', 'scp', 'usbkey'], aliases=['proto']),
        url=dict(type='str'),
        url_username=dict(type='str'),
        url_password=dict(type='str', no_log=True),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'absent', ['source']],
            ['state', 'present', ['protocol', 'source', 'url']],
        ],
    )

    polling_interval = module.params['polling_interval']
    protocol = module.params['protocol']
    state = module.params['state']
    source = module.params['source']
    url = module.params['url']
    url_password = module.params['url_password']
    url_username = module.params['url_username']

    aci = ACIModule(module)
    aci.construct_url(
        root_class=dict(
            aci_class='firmwareOSource',
            aci_rn='fabric/fwrepop',
            filter_target='eq(firmwareOSource.name, "{0}")'.format(source),
            module_object=source,
        ),
    )
    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(
            aci_class='firmwareOSource',
            class_config=dict(
                name=source,
                url=url,
                password=url_password,
                pollingInterval=polling_interval,
                proto=protocol,
                user=url_username,
            ),
        )

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='firmwareOSource')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
