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
module: opennms_requisition_category
author:
  - Danny Sonnenschein (@lxdicted)
version_added: "2.9"
short_description: Manage OpenNMS node's categories
description:
  - Add or delete OpenNMS categories to a node via REST API.
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
  state:
    description:
      - State of the category. If state is 'absent', the category is
      - going to be deleted.
    choices: [ absent, present ]
    default: present
  requisition:
    description:
      - Name of the node's requisition.
    required: true
  foreign_id:
    description:
      - Foreign ID of the node, either this or node_label is required.
  node_label:
    description:
      - The node label, either this or foreign_id is required.
  name:
    description:
      - The category name.
    required: true
    aliases: [category]
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
  - name: Add a category to a node
    opennms_requisition_category:
      requisition: requisition-name
      label: "{{ ansible_fqdn }}"
      name: "{{ ansible_virtualization_type }}"
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


def opennms_requisition_node_exists(module, data):

    # define http headers
    headers = opennms_headers(module, data)

    node_exists = False
    node = {}

    request_uri = '%s/rest/requisitions/%s/nodes' % (data['url'], data['requisition'])
    if data['foreign_id'] is not None:
        request_uri += '/%s' % data['foreign_id']

    r, info = fetch_url(module, request_uri, headers=headers, method="GET")
    if info['status'] == 200:
        nodes = json.loads(r.read())
        if data['foreign_id'] is not None:
            node = nodes
            node_exists = True
        elif nodes['count'] is not None:
            for n in nodes['node']:
                if n['node-label'] == data['node_label']:
                    node_exists = True
                    node = n

    return node_exists, node


def opennms_requisition_node_category_exists(module, data):

    # define http headers
    headers = opennms_headers(module, data)

    category_exists = False
    category = {}

    node_exists, node = opennms_requisition_node_exists(module, data)
    if node_exists is False:
        if data['foreign_id'] is None:
            label = data['node_label']
        else:
            label = data['foreign_id']
        module.fail_json(msg="Cannot find node '%s' in requisition '%s'" % (label, data['requisition']))

    for a in node['category']:
        if a['name'] == data['name']:
            category_exists = True
            category = a

    return category_exists, category, node['foreign-id']


def opennms_requisition_node_category_delete(module, data):

    # define http headers
    headers = opennms_headers(module, data)

    category_exists, category, foreign_id = opennms_requisition_node_category_exists(module, data)

    result = {}
    if category_exists is False:
        result['msg'] = "Category '%s' not defined for node '%s'" % (data['name'], foreign_id)
        result['changed'] = False
    else:
        if module.check_mode is True:
            result['msg'] = "Category '%s' for node '%s':'%s' would be deleted" % (data['name'], data['requisition'], foreign_id)
            result['changed'] = True
        else:
            request_uri = '%s/rest/requisitions/%s/nodes/%s/categories/%s' % (data['url'], data['requisition'], foreign_id, data['name'])
            r, info = fetch_url(module, request_uri, headers=headers, method='DELETE')
            if info['status'] == 202 or info['status'] == 204:
                result['msg'] = "Category '%s' for node '%s' deleted from requisition '%s'" % (data['name'], foreign_id, data['requisition'])
                result['changed'] = True
            else:
                msg = "Deletion of category '%s' for node '%s':'%s' failed (HTTP status: %i)" % (data['name'], data['requisition'], foreign_id, info['status'])
                module.fail_json(msg=msg)

    return result


def opennms_requisition_node_category_add(module, data):

    # define http headers
    headers = opennms_headers(module, data)

    category_exists, category, foreign_id = opennms_requisition_node_category_exists(module, data)

    result = {}
    if category_exists is True:
        result['msg'] = "Category '%s' for node '%s' in requisition '%s' not added" % (data['name'], foreign_id, data['requisition'])
        result['changed'] = False
    else:
        if module.check_mode is True:
            result['msg'] = "Category '%s' for node '%s':'%s' in would be added" % (data['name'], data['requisition'], foreign_id)
            result['changed'] = True
        else:
            content = {"name": data['name']}

            request_uri = "%s/rest/requisitions/%s/nodes/%s/categories" % (data['url'], data['requisition'], foreign_id)
            r, info = fetch_url(module, request_uri, headers=headers, method='POST', data=json.dumps(content))
            if info['status'] == 202:
                result['msg'] = "Category '%s' for node '%s' added in requisition '%s'" % (data['name'], foreign_id, data['requisition'])
                result['changed'] = True
            else:
                msg = "Addition of category '%s' for node '%s':'%s' failed (HTTP status: %i)" % (data['name'], data['requisition'], foreign_id, info['status'])
                module.fail_json(msg=msg)

    return result


def run_module():
    # use the predefined argument spec for url
    argument_spec = url_argument_spec()
    # remove unnecessary arguments
    del argument_spec['force']
    del argument_spec['force_basic_auth']
    del argument_spec['http_agent']
    argument_spec.update(
        state=dict(choices=['present', 'absent'], default='present'),
        url=dict(aliases=['opennms_url'], default='http://localhost:8980/opennms'),
        url_username=dict(aliases=['opennms_username'], default='admin'),
        url_password=dict(aliases=['opennms_password'], default='admin', no_log=True),
        requisition=dict(type='str', required=True),
        foreign_id=dict(type='str'),
        node_label=dict(type='str'),
        name=dict(aliases=['category'], type='str', required=True),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_together=[['url_username', 'url_password']],
        required_one_of=[['node_label', 'foreign_id']],
    )

    result = {}
    if module.params['state'] == 'absent':
        result = opennms_requisition_node_category_delete(module, module.params)
    elif module.params['state'] == 'present':
        result = opennms_requisition_node_category_add(module, module.params)

    module.exit_json(**result)

    return


def main():
    run_module()


if __name__ == '__main__':
    main()
