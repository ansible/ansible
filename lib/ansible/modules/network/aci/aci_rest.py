#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2015 Jason Edelman <jason@networktocode.com>, Network to Code, LLC
# Copyright 2017 Dag Wieers <dag@wieers.com>

# This file is part of Ansible by Red Hat
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
module: aci_rest
short_description: Direct access to the Cisco APIC REST API
description:
- Enables the management of the Cisco ACI fabric through direct access to the Cisco APIC REST API.
- More information regarding the Cisco APIC REST API is available from
  U(http://www.cisco.com/c/en/us/td/docs/switches/datacenter/aci/apic/sw/2-x/rest_cfg/2_1_x/b_Cisco_APIC_REST_API_Configuration_Guide.html).
author:
- Jason Edelman (@jedelman8)
- Dag Wieers (@dagwieers)
version_added: '2.4'
requirements:
- lxml (when using XML content)
- xmljson >= 0.1.8 (when using XML content)
options:
  hostname:
    description:
    - IP Address or hostname of APIC resolvable by Ansible control host.
    required: true
    aliases: [ host ]
  username:
    description:
    - Username used to login to the switch.
    required: true
    default: admin
    aliases: [ user ]
  password:
    description:
    - The password to use for authentication.
    required: true
  method:
    description:
    - The HTTP method of the request or response.
    required: true
    default: get
    choices: [ delete, get, post ]
    aliases: [ action ]
  path:
    description:
    - URI being used to execute API calls.
    - Must end in C(.xml) or C(.json).
    required: true
    aliases: [ uri ]
  src:
    description:
    - Name of the absolute path of the filname that includes the body
      of the http request being sent to the ACI fabric.
    aliases: [ config_file ]
  content:
    description:
    - When used instead of C(src), sets the content of the API request directly.
    - This may be convenient to template simple requests, for anything complex use the M(template) module.
  use_ssl:
    description:
    - If C(no), an HTTP connection will be used instead of the default HTTPS connection.
    type: bool
    default: 'yes'
  timeout:
    description:
    - The socket level timeout in seconds.
    default: 30
  validate_certs:
    description:
    - If C(no), SSL certificates will not be validated.
    - This should only set to C(no) used on personally controlled sites using self-signed certificates.
    type: bool
    default: 'yes'
notes:
- When using inline-JSON (using C(content)), YAML requires to start with a blank line.
- XML payloads require the C(lxml) and C(xmljson) python libraries. For JSON payloads nothing special is needed.
'''

EXAMPLES = r'''
- name: Add a tenant
  aci_rest:
    hostname: '{{ inventory_hostname }}'
    username: '{{ aci_username }}'
    password: '{{ aci_password }}'
    method: POST
    path: /api/mo/uni.xml
    src: /home/cisco/ansible/aci/configs/aci_config.xml
  delegate_to: localhost

- name: Get tenants
  aci_rest:
    hostname: '{{ inventory_hostname }}'
    username: '{{ aci_username }}'
    password: '{{ aci_password }}'
    method: GET
    path: /api/node/class/fvTenant.json
  delegate_to: localhost

- name: Configure contracts
  aci_rest:
    hostname: '{{ inventory_hostname }}'
    username: '{{ aci_username }}'
    password: '{{ aci_password }}'
    method: POST
    path: /api/mo/uni.xml
    src: /home/cisco/ansible/aci/configs/contract_config.xml
  delegate_to: localhost

- name: Register leaves and spines
  aci_rest:
    hostname: '{{ inventory_hostname }}'
    username: '{{ aci_username }}'
    password: '{{ aci_password }}'
    validate_certs: no
    method: POST
    path: /api/mo/uni/controller/nodeidentpol.xml
    content: |
      <fabricNodeIdentPol>
        <fabricNodeIdentP name="{{ item.name }}" nodeId="{{ item.nodeid }}" status="{{ item.status }}" serial="{{ item.serial }}"/>
      </fabricNodeIdentPol>
  with_items:
  - '{{ apic_leavesspines }}'
  delegate_to: localhost

- name: Wait for all controllers to become ready
  aci_rest:
    hostname: '{{ inventory_hostname }}'
    username: '{{ aci_username }}'
    password: '{{ aci_password }}'
    validate_certs: no
    path: /api/node/class/topSystem.json?query-target-filter=eq(topSystem.role,"controller")
  register: apics
  until: "'totalCount' in apics and apics.totalCount|int >= groups['apic']|count"
  retries: 120
  delay: 30
  delegate_to: localhost
  run_once: yes
'''

RETURN = r'''
data:
  description: The payload send to the APIC REST API (xml or json)
  returned: always
  type: string
  sample: '<foo bar="boo"/>'
error_code:
  description: The REST ACI return code, useful for troubleshooting on failure
  returned: always
  type: int
  sample: 122
error_text:
  description: The REST ACI descriptive text, useful for troubleshooting on failure
  returned: always
  type: string
  sample: unknown managed object class foo
imdata:
  description: Converted output returned by the APIC REST (register this for post-processing)
  returned: always
  type: string
  sample: [{"error": {"attributes": {"code": "122", "text": "unknown managed object class foo"}}}]
output:
  description: The raw output returned by the APIC REST API (xml or json)
  returned: always
  type: string
  sample: '<?xml version="1.0" encoding="UTF-8"?><imdata totalCount="1"><error code="122" text="unknown managed object class foo"/></imdata>'
response:
  description: HTTP response string
  returned: always
  type: string
  sample: 'HTTP Error 400: Bad Request'
status:
  description: HTTP status code
  returned: always
  type: int
  sample: 400
totalCount:
  description: Number of items in the imdata array
  returned: always
  type: int
  sample: 0
'''

import json
import os

# Optional, only used for XML payload
try:
    import lxml.etree
    HAS_LXML_ETREE = True
except ImportError:
    HAS_LXML_ETREE = False

# Optional, only used for XML payload
try:
    from xmljson import cobra
    HAS_XMLJSON_COBRA = True
except ImportError:
    HAS_XMLJSON_COBRA = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


def aci_response(rawoutput, rest_type='xml'):
    result = dict(
        output=rawoutput,
    )

    output = dict(
        imdata=dict(),
    )

    if rest_type == 'json':
        output = json.loads(rawoutput)
    else:
        # NOTE: The XML-to-JSON conversion is using the "Cobra" convention
        xml = lxml.etree.fromstring(rawoutput)
        imdata = cobra.data(xml)

        # Reformat as ACI does for JSON API output
        if 'children' in imdata['imdata']:
            output['imdata'] = imdata['imdata']['children']
        output['totalCount'] = imdata['imdata']['attributes']['totalCount']

    if 'imdata' in output:
        if int(output['totalCount']) > 0 and 'error' in output['imdata'][0]:
            result['error_code'] = output['imdata'][0]['error']['attributes']['code']
            result['error_text'] = output['imdata'][0]['error']['attributes']['text']
        else:
            result['error_code'] = 0
            result['error_text'] = 'Success'
    else:
        result['error_code'] = -1
        result['error_text'] = 'This should not happen'

    result.update(output)

    return result


def main():

    module = AnsibleModule(
        argument_spec=dict(
            hostname=dict(type='str', required=True, aliases=['host']),
            username=dict(type='str', default='admin', aliases=['user']),
            password=dict(type='str', required=True, no_log=True),
            path=dict(type='str', required=True, aliases=['uri']),
            method=dict(type='str', default='get', choices=['delete', 'get', 'post'], aliases=['action']),
            src=dict(type='path', aliases=['config_file']),
            content=dict(type='str'),
            timeout=dict(type='int', default=30),
            use_ssl=dict(type='bool', default=True),
            validate_certs=dict(type='bool', default=True),
        ),
        mutually_exclusive=[['content', 'src']],
        supports_check_mode=True,
    )

    hostname = module.params['hostname']
    username = module.params['username']
    password = module.params['password']

    path = module.params['path']
    content = module.params['content']
    src = module.params['src']

    use_ssl = module.params['use_ssl']
    method = module.params['method']
    timeout = module.params['timeout']

    result = dict(
        changed=False,
        data='',
        output='',
    )

    # Report missing file
    file_exists = False
    if src:
        if os.path.isfile(src):
            file_exists = True
        else:
            module.fail_json(msg='Cannot find/access src:\n%s' % src)

    # Find request type
    if path.find('.xml') != -1:
        rest_type = 'xml'
        if not HAS_LXML_ETREE:
            module.fail_json(msg='The lxml python library is missing, or lacks etree support.')
        if not HAS_XMLJSON_COBRA:
            module.fail_json(msg='The xmljson python library is missing, or lacks cobra support.')
    elif path.find('.json') != -1:
        rest_type = 'json'
    else:
        module.fail_json(msg='Failed to find REST API content type (neither .xml nor .json).')

    # Set protocol for further use
    if use_ssl:
        protocol = 'https'
    else:
        protocol = 'http'

    # Perform login first
    url = '%s://%s/api/aaaLogin.json' % (protocol, hostname)
    payload = {'aaaUser': {'attributes': {'name': username, 'pwd': password}}}
    resp, auth = fetch_url(module, url, data=json.dumps(payload), method='POST', timeout=timeout)

    # Connection or authentication failed
    if resp is None or auth['status'] != 200:

        if 'body' in auth:
            # Authentication failed
            result.update(aci_response(auth['body'], 'json'))
            result['msg'] = 'Authentication failed: %(error_code)s %(error_text)s' % result
        else:
            # Connection failed
            result['msg'] = '%(msg)s for %(url)s' % auth

        # Return normal Ansible URL related module responses
        result['response'] = auth['msg']
        result['status'] = auth['status'],
        module.fail_json(**result)

    # Prepare request data
    if content:
        result['data'] = content
    elif file_exists:
        with open(src, 'r') as config_object:
            result['data'] = config_object.read()

    # Ensure changes are reported
    if method in ('delete', 'post'):
        # FIXME: Hardcoding changed is not idempotent
        result['changed'] = True

        # In check_mode we assume it works, but we don't actually perform the requested change
        # TODO: Could we turn this request in a GET instead ?
        if module.check_mode:
            module.exit_json(response='OK (Check mode)', status=200, **result)
    else:
        result['changed'] = False

    # Perform actual request using auth cookie
    url = '%s://%s/%s' % (protocol, hostname, path.lstrip('/'))
    headers = dict(Cookie=resp.headers['Set-Cookie'])

    resp, info = fetch_url(module, url, data=result['data'], method=method.upper(), timeout=timeout, headers=headers)
    result['response'] = info['msg']
    result['status'] = info['status']

    # Report failure
    if info['status'] != 200:
        result.update(aci_response(info['body'], rest_type))
        result['msg'] = 'Task failed: %(error_code)s %(error_text)s' % result
        module.fail_json(**result)

    # Report success
    result.update(aci_response(resp.read(), rest_type))
    module.exit_json(**result)

if __name__ == '__main__':
    main()
