#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage PaloAltoNetworks Firewall
# (c) 2019, Tomi Raittinen <tomi.raittinen@gmail.com>
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
author:
    - Luigi Mori (@jtschichold)
    - Ivan Bojer (@ivanbojer)
    - Tomi Raittinen (@traittinen)
version_added: "2.3"
requirements:
    - pan-python
deprecated:
    alternative: Use U(https://galaxy.ansible.com/PaloAltoNetworks/paloaltonetworks) instead.
    removed_in: "2.12"
    why: Consolidating code base.
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device.
        required: true
    password:
        description:
            - Password for authentication. If the value is not specified in the
              task, the value of environment variable C(ANSIBLE_NET_PASSWORD)
              will be used instead.
        required: true
    username:
        description:
            - Username for authentication. If the value is not specified in the
              task, the value of environment variable C(ANSIBLE_NET_USERNAME)
              will be used instead if defined. C(admin) will be used if nothing
              above is defined.
        default: admin
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
    description:
        description:
            - Commit description/comment
        type: str
        version_added: "2.8"
    commit_changes_by:
        description:
            - Commit changes made by specified admin
        type: list
        version_added: "2.8"
    commit_vsys:
        description:
            - Commit changes for specified VSYS
        type: list
        version_added: "2.8"
'''

EXAMPLES = '''
# Commit candidate config on 192.168.1.1 in sync mode
- panos_commit:
    ip_address: "192.168.1.1"
    username: "admin"
    password: "admin"
'''

RETURN = '''
panos_commit:
    description: Information about commit job.
    returned: always
    type: complex
    version_added: 2.8
    contains:
        job_id:
            description: Palo Alto job ID for the commit operation. Only returned if commit job is launched on device.
            returned: always
            type: str
            sample: "139"
        status_code:
            description: Palo Alto API status code. Null if commit is successful.
            returned: always
            type: str
            sample: 19
        status_detail:
            description: Palo Alto API detailed status message.
            returned: always
            type: str
            sample: Configuration committed successfully
        status_text:
            description: Palo Alto API status text.
            returned: always
            type: str
            sample: success
'''

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


from ansible.module_utils.basic import AnsibleModule, env_fallback
import xml.etree.ElementTree as etree

try:
    import pan.xapi
    HAS_LIB = True
except ImportError:
    HAS_LIB = False


def main():
    argument_spec = dict(
        ip_address=dict(required=True, type='str'),
        password=dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), no_log=True),
        username=dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME']), default="admin"),
        interval=dict(default=0.5),
        timeout=dict(),
        sync=dict(type='bool', default=True),
        description=dict(type='str'),
        commit_changes_by=dict(type='list'),
        commit_vsys=dict(type='list')
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_LIB:
        module.fail_json(msg='pan-python is required for this module')

    ip_address = module.params["ip_address"]
    if not ip_address:
        module.fail_json(msg="ip_address should be specified")

    password = module.params["password"]
    if not password:
        module.fail_json(msg="password is required")

    username = module.params['username']
    if not username:
        module.fail_json(msg="username is required")

    interval = module.params['interval']
    timeout = module.params['timeout']
    sync = module.params['sync']

    xapi = pan.xapi.PanXapi(
        hostname=ip_address,
        api_username=username,
        api_password=password
    )

    cmd = "<commit>"

    description = module.params["description"]
    if description:
        cmd += "<description>" + description + "</description>"

    commit_changes_by = module.params["commit_changes_by"]
    commit_vsys = module.params["commit_vsys"]

    if commit_changes_by or commit_vsys:

        cmd += "<partial>"

        if commit_changes_by:
            cmd += "<admin>"
            for admin in commit_changes_by:
                cmd += "<member>" + admin + "</member>"
            cmd += "</admin>"

        if commit_vsys:
            cmd += "<vsys>"
            for vsys in commit_vsys:
                cmd += "<member>" + vsys + "</member>"
            cmd += "</vsys>"

        cmd += "</partial><force></force>"

    cmd += "</commit>"

    xapi.commit(
        cmd=cmd,
        sync=sync,
        interval=interval,
        timeout=timeout
    )

    try:
        result = xapi.xml_root().encode('utf-8')
        root = etree.fromstring(result)
        job_id = root.find('./result/job/id').text
    except AttributeError:
        job_id = None

    panos_commit_details = dict(
        status_text=xapi.status,
        status_code=xapi.status_code,
        status_detail=xapi.status_detail,
        job_id=job_id
    )

    if "Commit failed" in xapi.status_detail:
        module.fail_json(msg=xapi.status_detail, panos_commit=panos_commit_details)

    if job_id:
        module.exit_json(changed=True, msg="Commit successful.", panos_commit=panos_commit_details)
    else:
        module.exit_json(changed=False, msg="No changes to commit.", panos_commit=panos_commit_details)


if __name__ == '__main__':
    main()
