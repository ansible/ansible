#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2019, Danny Sonnenschein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.1'
}

DOCUMENTATION = '''
---
module: opennms_requisition
author:
  - Danny Sonnenschein (@lxdicted)
version_added: "2.9"
short_description: Manage OpenNMS requisitions
description:
  - Create, synchronize, delete OpenNMS requisitions via REST API.
options:
  url:
    description:
      - The OpenNMS REST API  URL
    default: http://localhost:8980/opennms
    aliases: [opennms_url]
  url_username:
    description:
      - The OpenNMS API user name.
    default: admin
    aliases: [opennms_username]
  url_password:
    description:
      - The OpenNMS API user's password.
    default: admin
    aliases: [opennms_password]
  synchronize:
    description:
      - If the requisition should be synchronized
    type: bool
    default: false
  rescan_existing:
    description:
      - If existing node should be rescaned during synchronization
    type: bool
    default: true
  date_stamp:
    description:
      - Timestamp of requisition creation
    required: true
  state:
    description:
      - State of the requisition
    choices: [ absent, present ]
    default: present
  name:
    description:
      - The name of the requisition.
    required: true
    aliases: [requisition]
  client_cert:
    description:
      - PEM formatted certificate chain file to be used for SSL client authentication.
      - This file can also include the key as well, and if the key is included, client_key is not required.
  client_key:
    description:
      - PEM formatted file that contains your private key to be used for SSL client authentication.
      - If client_cert contains both the certificate and key, this option is not required.
  use_proxy:
    description:
      - If no, it will not use a proxy, even if one is defined in an environment variable on the target hosts.
    type: bool
    default: true
  validate_certs:
    description:
      - If no, TLS certificates will not be validated.
      - This should only be used on personally controlled devices using self-signed certificates.
    type: bool
    default: true
'''

EXAMPLES = '''
    - name: Create an empty requisition
      opennms_requisition:
        opennms_username: ansible
        opennms_password: password
        name: ansible

    - name: Add a node to the requisition
      opennms_node:
        opennms_url: https://opennms.example.com/opennms
        node_label: nodename
        foreign_id: "{{ ansible_machine_id }}"
        name: ansible

    - name: Synchronize the requisition
      opennms_requisition:
        opennms_url: https://opennms.example.com/opennms
        opennms_username: admin
        opennms__password: admin
        name: ansible
        rescan_existing: false
        synchronize: true

    - name: Delete the requisition
      opennms_requisition:
        name: ansible
'''

RETURN = '''
msg:
    description: The result of the operation
    returned: success
    type: str
'''


import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url, url_argument_spec
from ansible.module_utils._text import to_native
from ansible.module_utils._text import to_text

__metaclass__ = type


def opennms_headers(module, data):

    headers = {
        'content-type': 'application/json; charset=utf8',
        'accept': 'application/json'
    }

    module.params['force_basic_auth'] = True

    return headers


def opennms_requisition_exists(module, data):

    # define http headers
    headers = opennms_headers(module, data)

    requisition_exists = False
    requisition = {}

    r, info = fetch_url(module, "%s/rest/requisitions/%s" % (data['url'], data['name']), headers=headers, method="GET")
    if info['status'] == 200:
        requisition_exists = True
        requisition = json.loads(r.read())

    return requisition_exists, requisition


def opennms_requisition_synchronize(module, data):

    # define http headers
    headers = opennms_headers(module, data)

    result = {}
    if module.check_mode is True:
        result['msg'] = "Requisition '%s' will be always synchronized" % data['name']
        result['changed'] = True
    else:
        request_uri = '%s/rest/requisitions/%s/import' % (data['url'], data['name'])
        if data['rescan_existing'] is False:
            request_uri += '?rescanExisting=false'

        r, info = fetch_url(module, request_uri, headers=headers, method='PUT')
        if info['status'] == 202:
            result['msg'] = "Requisition '%s' synchronized" % data['name']
            result['changed'] = True
        elif info['status'] == 204:
            result['msg'] = "Requisition '%s' already synchronized" % data['name']
            result['changed'] = False
        else:
            module.fail_json(msg="Synchronization of requisition '%s' failed (HTTP status: %i)" % (data['name'], info['status']))

    return result


def opennms_requisition_create(module, data):

    # define http headers
    headers = opennms_headers(module, data)

    # test if requisition already exists
    requisition_exists, requisition = opennms_requisition_exists(module, data)

    result = {}
    if requisition_exists is True:
        result['msg'] = "Requisition '%s' not modified" % data['name']
        result['changed'] = False
    else:
        if module.check_mode is True:
            result['msg'] = "Requisition '%s' would be created" % data['name']
            result['changed'] = True
        else:
            content = {'foreign-source': data['name'], 'node': []}

            request_uri = "%s/rest/requisitions" % data['url']
            r, info = fetch_url(module, request_uri, headers=headers, method='POST', data=json.dumps(content))
            if info['status'] == 202:
                result['msg'] = "Requisition '%s' created" % data['name']
                result['changed'] = True
            else:
                module.fail_json(msg="Creation of requisition '%s' failed (HTTP status: %i)" % (data['name'], info['status']))

    return result


def opennms_requisition_delete(module, data):

    # define http headers
    headers = opennms_headers(module, data)

    # test if requisition exists
    requisition_exists, requisition = opennms_requisition_exists(module, data)

    result = {}
    if requisition_exists is True:
        if module.check_mode is True:
            result['msg'] = "Requisition '%s' would be deleted" % data['name']
            result['changed'] = True
        else:
            request_uri = '%s/rest/requisitions/%s' % (data['url'], data['name'])
            r, info = fetch_url(module, '%s/rest/requisitions/%s' % (data['url'], data['name']), headers=headers, method='DELETE')
            if info['status'] == 202:
                result['msg'] = "Requisition '%s' deleted" % data['name']
                result['changed'] = True

                request_uri = '%s/rest/requisitions/deployed/%s' % (data['url'], data['name'])
                fetch_url(module, request_uri, headers=headers, method='DELETE')
                request_uri = '%s/rest/foreignSources/%s' % (data['url'], data['name'])
                fetch_url(module, request_uri, headers=headers, method='DELETE')
                request_uri = '%s/rest/foreignSources/deployed/%s' % (data['url'], data['name'])
                fetch_url(module, request_uri, headers=headers, method='DELETE')
            else:
                module.fail_json(msg="Deletion of requisition '%s' failed (HTTP status: %i)" % (data['name'], info['status']))
    else:
        result['msg'] = "Requisition '%s' not found" % data['name']
        result['changed'] = False

    return result


def run_module():
    # use the predefined argument spec for url
    argument_spec = url_argument_spec()
    # remove unnecessary arguments
    del argument_spec['force']
    del argument_spec['http_agent']
    del argument_spec['force_basic_auth']
    argument_spec.update(
        state=dict(choices=['present', 'absent'], default='present'),
        url=dict(aliases=['opennms_url'], default='http://localhost:8980/opennms'),
        url_username=dict(aliases=['opennms_username'], default='admin'),
        url_password=dict(aliases=['opennms_password'], default='admin', no_log=True),
        name=dict(aliases=['requisition'], type='str', required=True),
        date_stamp=dict(type='str', required=False),
        synchronize=dict(type='bool', default=False),
        rescan_existing=dict(type='bool', default=True)
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_together=[['url_username', 'url_password']]
    )

    if module.params['state'] == 'absent':
        result = opennms_requisition_delete(module, module.params)
    elif module.params['state'] == 'present':
        result = opennms_requisition_create(module, module.params)
        if module.params['synchronize']:
            result = opennms_requisition_synchronize(module, module.params)

    module.exit_json(**result)

    return


def main():
    run_module()


if __name__ == '__main__':
    main()
