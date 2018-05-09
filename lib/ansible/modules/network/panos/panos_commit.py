#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage PaloAltoNetworks Firewall
# (c) 2016, techbizdev <techbizdev@paloaltonetworks.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: panos_commit
short_description: commit firewall's candidate configuration
description:
    - PanOS module that will commit firewall's candidate configuration on
    - the device. The new configuration will become active immediately.
author: "Luigi Mori (@jtschichold), Ivan Bojer (@ivanbojer)"
version_added: "2.3"
requirements:
    - pan-python
options:
    interval:
        description:
            - interval for checking commit job
        default: 0.5
    timeout:
        description:
            - timeout for commit job
    sync:
        description:
            - if commit should be synchronous
        type: bool
        default: 'yes'
extends_documentation_fragment: panos
'''

EXAMPLES = '''
# Commit candidate config on 192.168.1.1 in sync mode
- panos_commit:
    ip_address: "192.168.1.1"
    username: "admin"
    password: "admin"
'''

RETURN = '''
status:
    description: success status
    returned: success
    type: string
    sample: "okey dokey"
'''

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


from ansible.module_utils.basic import AnsibleModule

try:
    import pan.xapi
    HAS_LIB = True
except ImportError:
    HAS_LIB = False


def main():
    argument_spec = dict(
        ip_address=dict(),
        password=dict(no_log=True),
        username=dict(default='admin'),
        interval=dict(default=0.5),
        timeout=dict(),
        sync=dict(type='bool', default=True)
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_LIB:
        module.fail_json(msg='pan-python required for this module')

    ip_address = module.params["ip_address"]
    if not ip_address:
        module.fail_json(msg="ip_address should be specified")
    password = module.params["password"]
    if not password:
        module.fail_json(msg="password is required")
    username = module.params['username']

    interval = module.params['interval']
    timeout = module.params['timeout']
    sync = module.params['sync']

    xapi = pan.xapi.PanXapi(
        hostname=ip_address,
        api_username=username,
        api_password=password
    )

    xapi.commit(
        cmd="<commit></commit>",
        sync=sync,
        interval=interval,
        timeout=timeout
    )

    module.exit_json(changed=True, msg="okey dokey")

if __name__ == '__main__':
    main()
