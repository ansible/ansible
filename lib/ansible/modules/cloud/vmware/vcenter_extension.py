#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Michael Tipton <mike () ibeta.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: vcenter_extension
short_description: Register/deregister vCenter Extensions
description:
    - This module can be used to register/deregister vCenter Extensions.
version_added: 2.8
author:
    - Michael Tipton (@castawayegr)
notes:
    - Tested on vSphere 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
  extension_key:
    description:
    - The extension key of the extension to install or uninstall.
    required: True
    type: str
  version:
    description:
    - The version of the extension you are installing or uninstalling.
    required: True
    type: str
  name:
    description:
    - Required for C(state=present). The name of the extension you are installing.
    type: str
  company:
    description:
    - Required for C(state=present). The name of the company that makes the extension.
    type: str
  description:
    description:
    - Required for C(state=present). A short description of the extension.
    type: str
  email:
    description:
    - Required for C(state=present). Administrator email to use for extension.
    type: str
  url:
    description:
    - Required for C(state=present). Link to server hosting extension zip file to install.
    type: str
  ssl_thumbprint:
    description:
    - Required for C(state=present). SSL thumbprint of the extension hosting server.
    type: str
  server_type:
    description:
    - Required for C(state=present). Type of server being used to install the extension (SOAP, REST, HTTP, etc.).
    default: vsphere-client-serenity
    type: str
  client_type:
    description:
    - Required for C(state=present). Type of client the extension is (win32, .net, linux, etc.).
    default: vsphere-client-serenity
    type: str
  visible:
    description:
    - Show the extension in solution manager inside vCenter.
    default: True
    type: bool
  state:
    description:
    - Add or remove vCenter Extension.
    choices: [absent, present]
    default: present
    type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
    - name: Register vCenter Extension
      vcenter_extension:
         hostname: "{{ groups['vcsa'][0] }}"
         username: "{{ vcenter_username }}"
         password: "{{ site_password }}"
         extension_key: "{{ extension_key }}"
         version: "1.0"
         company: "Acme"
         name: "Acme Extension"
         description: "acme management"
         email: "user@example.com"
         url: "https://10.0.0.1/ACME-vSphere-web-plugin-1.0.zip"
         ssl_thumbprint: "{{ ssl_thumbprint }}"
         state: present
      delegate_to: localhost
      register: register_extension

    - name: Deregister vCenter Extension
      vcenter_extension:
         hostname: "{{ groups['vcsa'][0] }}"
         username: "{{ vcenter_username }}"
         password: "{{ site_password }}"
         extension_key: "{{ extension_key }}"
         version: "1.0"
         state: absent
      delegate_to: localhost
      register: deregister_extension
'''

RETURN = """
result:
    description: information about performed operation
    returned: always
    type: str
    sample: "'com.acme.Extension' installed."
"""

try:
    from pyVmomi import vim
except ImportError:
    pass

import datetime

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import connect_to_api, vmware_argument_spec


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        extension_key=dict(type='str', required=True),
        version=dict(type='str', required=True),
        email=dict(type='str', required=False),
        description=dict(type='str', required=False),
        company=dict(type='str', required=False),
        name=dict(type='str', required=False),
        url=dict(type='str', required=False),
        ssl_thumbprint=dict(type='str', required=False),
        client_type=dict(type='str', default='vsphere-client-serenity', required=False),
        server_type=dict(type='str', default='vsphere-client-serenity', required=False),
        visible=dict(type='bool', default='True', required=False),
        state=dict(type='str', default='present', choices=['absent', 'present']),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        required_if=[
            ['state', 'present', ['email', 'description', 'company', 'name', 'url', 'ssl_thumbprint', 'server_type', 'client_type']]
        ]
    )

    state = module.params['state']
    extension_key = module.params['extension_key']
    version = module.params['version']
    email = module.params['email']
    desc = module.params['description']
    name = module.params['name']
    company = module.params['company']
    client_type = module.params['client_type']
    server_type = module.params['server_type']
    url = module.params['url']
    visible = module.params['visible']
    thumbprint = module.params['ssl_thumbprint']

    content = connect_to_api(module, False)
    em = content.extensionManager
    key_check = em.FindExtension(extension_key)
    results = dict(changed=False, installed=dict())

    if state == 'present' and key_check:
        results['changed'] = False
        results['installed'] = "'%s' is already installed" % (extension_key)

    elif state == 'present' and not key_check:
        extension = vim.Extension()
        extension.key = extension_key
        extension.company = company
        extension.version = version
        extension.lastHeartbeatTime = datetime.datetime.now()
        description = vim.Description()
        description.label = name
        description.summary = desc
        extension.description = description
        extension.shownInSolutionManager = visible

        client = vim.Extension.ClientInfo()
        client.company = company
        client.version = version
        client.description = description
        client.type = client_type
        client.url = url
        extension.client = [client]

        server = vim.Extension.ServerInfo()
        server.company = company
        server.description = description
        server.type = server_type
        server.adminEmail = email
        server.serverThumbprint = thumbprint
        server.url = url
        extension.server = [server]

        em.RegisterExtension(extension)
        results['changed'] = True
        results['installed'] = "'%s' installed." % (extension_key)

    elif state == 'absent' and key_check:
        em.UnregisterExtension(extension_key)
        results['changed'] = True
        results['installed'] = "'%s' uninstalled." % (extension_key)

    elif state == 'absent' and not key_check:
        results['changed'] = False
        results['installed'] = "'%s' is not installed." % (extension_key)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
