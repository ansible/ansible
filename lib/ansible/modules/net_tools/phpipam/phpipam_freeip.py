#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Carson Anderson <rcanderson23@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import print_function

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: phpipam_freeip
author: "Carson Anderson (@rcanderson23)"
short_description: Obtain free ip address
requirements: []
version_added: "2.7"
description:
    - Obtain first free ip address in a subnet from phpIPAM instance
options:
    username:
        description:
            - username that has permission to access phpIPAM API
        required: True
    password:
        description:
            - password for username provided
        required: True
    url:
        description:
            - API url for phpIPAM instance
        required: True
    subnet:
        description:
            - Subnet to obtain ip address from.
            - Must be in CIDR format.
        required: True
    section:
        description:
            - Section name that the subnet resides in.
        type: string
        required: True
    hostname:
        description:
            - Hostname displayed next to address in phpIPAM.
        type: string
        required: False
    description
        description:
            - Optional description displayed next to address in phpIPAM.
        type: string
        required: False
'''

EXAMPLES = '''

- name: Obtain next free ip address
  phpipam_freeip:
    username: username
    password: secret
    url: "https://ipam.domain.tld/api/app/"
    subnet: "192.168.10.0/24"
    hostname: "newhost"
    description: "optional description"
  register: new_ip

- name: print obtained ip address
  debug:
    msg: "IP Obtained {{ new_ip.ip }}"
'''

RETURN = '''
ip:
    description: string containing ip address
    returned: success
    type: simple
output:
    description: dictionary containing phpIPAM response
    returned: success
    type: complex
    contains:
        code:
            description: HTTP response code
            returned: success
            type: int
            sample: 201
        success:
            description: True or False depending on if ip was successfully obtained
            returned: success
            type: bool
            sample: True
        time:
            description: Amount of time operation took.
            returned: success
            type: float
            sample: 0.015
        message:
            description: Response message of what happened
            returned: success
            type: string
            sample: "Address created"
        data:
            description: Contains ip address obtained
            returned: success
            type: string
            sample: "192.168.10.2"
        id:
            description: ID of address created
            returned: success
            type: string
            sample: "206"
'''


from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.phpipam as phpipam
import urllib
import json


def main():
    module = AnsibleModule(
        argument_spec=dict(
            username=dict(type=str, required=True),
            password=dict(type=str, required=True, no_log=True),
            url=dict(type=str, required=True),
            subnet=dict(type=str, required=True),
            section=dict(type=str, required=True),
            hostname=dict(type=str, required=False),
            description=dict(type=str, required=False)
        ),
        supports_check_mode=False
    )

    result = dict(
        changed=False
    )
    username = module.params['username']
    password = module.params['password']
    url = module.params['url']
    subnet = module.params['subnet']
    section = module.params['section']
    hostname = module.params['hostname']
    description = module.params['description']

    session = phpipam.PhpIpamWrapper(username, password, url)
    try:
        session.create_session()
    except AttributeError:
        module.fail_json(msg='Error getting authorization token', **result)
    subnet_response = session.get_subnet(subnet, section)
    if subnet_response:
        url += 'addresses/first_free/'
        subnet_id = session.get_subnet_id(subnet, section)
        payload = urllib.urlencode({'subnetId': subnet_id,
                                    'hostname': hostname,
                                    'description': description})
        free_ip = json.load(session.post(url, payload))
        if free_ip['success']:
            ip = free_ip['data']
            result['ip'] = ip
            result['output'] = free_ip
            module.exit_json(**result)
        else:
            module.fail_json(msg='Subnet is full', **result)
    else:
        module.fail_json(msg='Subnet or section doesn\'t exist', **result)


if __name__ == '__main__':
    main()
