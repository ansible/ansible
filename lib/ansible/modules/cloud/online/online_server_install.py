#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: online_server_install
short_description: Install an Online server
description:
  - Gather facts about the servers.
  - U(https://www.online.net/en/dedicated-server)
version_added: "2.8"
author:
  - "Ludovic Petetin (@broferek)"
extends_documentation_fragment: online
options:
  host:
    description:
      - the Online server ID
    required: true
  os_id:
    description:
      - the OS ID
      - IDs can be retrieved from this API call https://api.online.net/api/v1/server/operatingSystems/<host>
    required: true
  hostname:
    description:
      - the server FQDN
    required: true
  root_password:
    description:
      - the password of the root user
    required: true
  user_login:
    description:
      - an Unix user to create on the server
    required: true
  user_password:
    description:
      - the password of the Unix user
    required: true
  partitioning_template_ref:
    description:
      - the partitioning template reference
      - the template reference can be found in https://console.online.net/fr/template/partition?os_type=linux
    required: true
'''

EXAMPLES = r'''
- name: Install Centos on the server 5824 with the user foo created
  online_server_install:
    api_token: "qsfda9964-foo-sghz8751-bar"
    host: "5824"
    os_id: 305
    hostname: "sd-5824"
    root_password: "root_bar"
    user_login: "foo"
    user_password: "bar"
    partitioning_template_ref: "ax686-foo-qsdf84-bar"
'''

RETURN = r'''
---
msg:
    description: Message specifying that the installation has started
    returned: success
    type: string
    sample: The installation has started. Check your server state at https://api.online.net/fr/server/state/5824
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.online import (
    Online, OnlineException, online_argument_spec
)


class OnlineServerInstall(Online):

    def __init__(self, module):
        super(OnlineServerInstall, self).__init__(module)
        host = module.params['host']
        self.name = 'api/v1/server/' + host


def main():
    argument_spec = online_argument_spec()
    argument_spec.update(
        dict(
            host=dict(
                required=True
            ),
            os_id=dict(
                required=True,
                type='int'
            ),
            hostname=dict(
                required=True
            ),
            root_password=dict(
                required=True,
                no_log=True
            ),
            user_login=dict(
                required=True
            ),
            user_password=dict(
                required=True,
                no_log=True
            ),
            partitioning_template_ref=dict(
                required=True
            )
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    host = module.params['host']
    post_data = dict(
        os_id=module.params['os_id'],
        hostname=module.params['hostname'],
        root_password=module.params['root_password'],
        user_login=module.params['user_login'],
        user_password=module.params['user_password'],
        partitioning_template_ref=module.params['partitioning_template_ref']
    )

    online = Online(module)

    # Retrieve os_id
    online.name = 'api/v1/server/operatingSystems/' + host
    try:
        online_os_ids_servers = list(filter(lambda d: d['type'] in ['server'], online.get_resources()))
    except OnlineException as exc:
        module.fail_json(msg=exc.message)

    online_os_id = ""
    available_os = list()
    for online_os_ids_server in online_os_ids_servers:
        if post_data['os_id'] == online_os_ids_server['id']:
            online_os_id = online_os_ids_server['id']
        available_os.append('{0} ({1}) [{2}]'.format(online_os_ids_server['version'], online_os_ids_server['arch'], str(online_os_ids_server['id'])))

    if not online_os_id:
        raise OnlineException('The list of available OS (arch) [os_id] is : {0}'.format(','.join(available_os)))

    # Send server install command
    online.name = 'api/v1/server/install/' + host
    try:
        online.post_resources(data=post_data)
    except OnlineException as exc:
        module.fail_json(msg=exc.message)

    module.exit_json(
        changed=True,
        msg="The installation has started. Check your server state at {0}/fr/server/state/{1}".format(module.params.get('api_url'), host)
    )


if __name__ == '__main__':
    main()
