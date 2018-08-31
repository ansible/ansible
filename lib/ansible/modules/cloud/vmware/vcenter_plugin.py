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
module: vcenter_plugin
short_description: Register/deregister vCenter Plugins
description:
    - This module can be used to register/deregister vCenter plugins.
version_added: 2.7
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
    - The extension key of the plugin to install or uninstall.
    required: True
  version:
    description:
    - The version of the plugin you are installing or uninstalling.
    required: True
  name:
    description:
    - Required for C(state=present). The name of the plugin you are installing.
  company:
    description:
    - Required for C(state=present). The name of the company that makes the plugin.
  description:
    description:
    - Required for C(state=present). A short description of the plugin.
  email:
    description:
    - Required for C(state=present). Administrator Email to use for Plugin.
  url:
    description:
    - Required for C(state=present). Link to server hosting plugin zip file to install.
  ssl_thumbprint:
    description:
    - Required for C(state=present). SSL thumbprint of the plugin hosting server.
  type:
    description:
    - Required for C(state=present). Type of plugin being installed (SOAP, REST, HTTP).
    default: vsphere-client-serenity
  state:
    description:
    - Add or remove vCenter Plugin.
    choices: [absent, present]
    default: present
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: vCenter Plugin Examples
  hosts: deploy_node
  tags:
    - plugins
  tasks:

    - name: Register vCenter Plugin
      vcenter_plugin:
         hostname: "{{ groups['vcsa'][0] }}"
         username: "{{ vcenter_username }}"
         password: "{{ site_password }}"
         extension_key: "{{ extension_key }}"
         version: "1.0"
         company: "Acme"
         name: "Acme Plugin"
         description: "acme management"
         email: "user@example.com"
         url: "https://10.0.0.1/ACME-vSphere-web-plugin-1.0.zip"
         ssl_thumbprint: "{{ ssl_thumbprint }}"
         state: present
      delegate_to: localhost
      register: register_plugin

    - name: Deregister vCenter Plugin
      vcenter_plugin:
         hostname: "{{ groups['vcsa'][0] }}"
         username: "{{ vcenter_username }}"
         password: "{{ site_password }}"
         extension_key: "{{ extension_key }}"
         version: "1.0"
         state: absent
      delegate_to: localhost
      register: deregister_plugin
'''

try:
    from pyVmomi import vim, vmodl
    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False

try:
    import datetime
    HAS_DT = True
except ImportError:
    HAS_DT = False


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (HAS_PYVMOMI, connect_to_api, vmware_argument_spec)


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
        type=dict(type='str', default='vsphere-client-serenity', required=False),
        state=dict(type='str', default='present', choices=['absent', 'present']),
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)

    if not HAS_PYVMOMI:
        module.fail_json(msg='pyvmomi is required for this module')

    if not HAS_DT:
        module.fail_json(msg='datetime is required for this module')

    state = module.params['state']
    extension_key = module.params['extension_key']
    version = module.params['version']
    email = module.params['email']
    desc = module.params['description']
    name = module.params['name']
    company = module.params['company']
    type = module.params['type']
    url = module.params['url']
    thumbprint = module.params['ssl_thumbprint']

    try:
        content = connect_to_api(module, False)
        em = content.extensionManager
        key_check = em.FindExtension(extension_key)
        results = dict(changed=False, result=dict())

        if state == 'present' and key_check:
            results['changed'] = False
            results['result'] = "'%s' is already installed" % (extension_key)

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
            extension.shownInSolutionManager = False

            client = vim.Extension.ClientInfo()
            client.company = company
            client.version = version
            client.description = description
            client.type = type
            client.url = url
            extension.client = [client]

            server = vim.Extension.ServerInfo()
            server.company = company
            server.description = description
            server.type = type
            server.adminEmail = email
            server.serverThumbprint = thumbprint
            server.url = url
            extension.server = [server]

            em.RegisterExtension(extension)
            results['changed'] = True
            results['result'] = "'%s' installed" % (extension_key)

        elif state == 'absent' and key_check:
            em.UnregisterExtension(extension_key)
            results['changed'] = True
            results['result'] = "'%s' uninstalled" % (extension_key)

        elif state == 'absent' and not key_check:
            results['changed'] = False
            results['result'] = "'%s' is not installed" % (extension_key)

        module.exit_json(**results)

    except vmodl.RuntimeFault as runtime_fault:
        module.fail_json(msg=runtime_fault.msg)
    except vmodl.MethodFault as method_fault:
        module.fail_json(msg=method_fault.msg)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
