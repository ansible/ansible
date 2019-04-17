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
module: panos_check
short_description: check if PAN-OS device is ready for configuration
description:
    - Check if PAN-OS device is ready for being configured (no pending jobs).
    - The check could be done once or multiple times until the device is ready.
author: "Luigi Mori (@jtschichold), Ivan Bojer (@ivanbojer)"
version_added: "2.3"
requirements:
    - pan-python
deprecated:
    alternative: Use U(https://galaxy.ansible.com/PaloAltoNetworks/paloaltonetworks) instead.
    removed_in: "2.12"
    why: Consolidating code base.
options:
    timeout:
        description:
            - timeout of API calls
        required: false
        default: 0
    interval:
        description:
            - time waited between checks
        required: false
        default: 0
extends_documentation_fragment: panos
'''

EXAMPLES = '''
# single check on 192.168.1.1 with credentials admin/admin
- name: check if ready
  panos_check:
    ip_address: "192.168.1.1"
    password: "admin"

# check for 10 times, every 30 seconds, if device 192.168.1.1
# is ready, using credentials admin/admin
- name: wait for reboot
  panos_check:
    ip_address: "192.168.1.1"
    password: "admin"
  register: result
  until: result is not failed
  retries: 10
  delay: 30
'''

RETURN = '''
# Default return values
'''

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


from ansible.module_utils.basic import AnsibleModule
import time

try:
    import pan.xapi
    HAS_LIB = True
except ImportError:
    HAS_LIB = False


def check_jobs(jobs, module):
    job_check = False
    for j in jobs:
        status = j.find('.//status')
        if status is None:
            return False
        if status.text != 'FIN':
            return False
        job_check = True
    return job_check


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(required=True, no_log=True),
        username=dict(default='admin'),
        timeout=dict(default=0, type='int'),
        interval=dict(default=0, type='int')
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)
    if not HAS_LIB:
        module.fail_json(msg='pan-python is required for this module')

    ip_address = module.params["ip_address"]
    password = module.params["password"]
    username = module.params['username']
    timeout = module.params['timeout']
    interval = module.params['interval']

    xapi = pan.xapi.PanXapi(
        hostname=ip_address,
        api_username=username,
        api_password=password,
        timeout=60
    )

    checkpnt = time.time() + timeout
    while True:
        try:
            xapi.op(cmd="show jobs all", cmd_xml=True)
        except Exception:
            pass
        else:
            jobs = xapi.element_root.findall('.//job')
            if check_jobs(jobs, module):
                module.exit_json(changed=True, msg="okey dokey")

        if time.time() > checkpnt:
            break

        time.sleep(interval)

    module.fail_json(msg="Timeout")


if __name__ == '__main__':
    main()
