#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_rest
short_description: Direct access to the Cisco APIC REST API
description:
- Enables the management of the Cisco ACI fabric through direct access to the Cisco APIC REST API.
- More information regarding the Cisco APIC REST API is available from
  U(http://www.cisco.com/c/en/us/td/docs/switches/datacenter/aci/apic/sw/2-x/rest_cfg/2_1_x/b_Cisco_APIC_REST_API_Configuration_Guide.html).
author:
- Dag Wieers (@dagwieers)
- Swetha Chunduri (@schunduri)
version_added: '2.4'
requirements:
- lxml (when using XML content)
- xmljson >= 0.1.8 (when using XML content)
- python 2.7+ (when using xmljson)
extends_documentation_fragment: aci
options:
  method:
    description:
    - The HTTP method of the request.
    - Using C(delete) is typically used for deleting objects.
    - Using C(get) is typically used for querying objects.
    - Using C(post) is typically used for modifying objects.
    required: yes
    default: get
    choices: [ delete, get, post ]
    aliases: [ action ]
  path:
    description:
    - URI being used to execute API calls.
    - Must end in C(.xml) or C(.json).
    required: yes
    aliases: [ uri ]
  content:
    description:
    - When used instead of C(src), sets the content of the API request directly.
    - This may be convenient to template simple requests, for anything complex use the M(template) module.
  src:
    description:
    - Name of the absolute path of the filname that includes the body
      of the http request being sent to the ACI fabric.
    aliases: [ config_file ]
notes:
- When using inline-JSON (using C(content)), YAML requires to start with a blank line.
  Otherwise the JSON statement will be parsed as a YAML mapping (dictionary) and translated into invalid JSON as a result.
- XML payloads require the C(lxml) and C(xmljson) python libraries. For JSON payloads nothing special is needed.
'''

EXAMPLES = r'''
- name: Add a tenant
  aci_rest:
    hostname: '{{ inventory_hostname }}'
    username: '{{ aci_username }}'
    password: '{{ aci_password }}'
    method: post
    path: /api/mo/uni.xml
    src: /home/cisco/ansible/aci/configs/aci_config.xml
  delegate_to: localhost

- name: Add a tenant using inline YAML
  aci_rest:
    hostname: '{{ inventory_hostname }}'
    username: '{{ aci_username }}'
    password: '{{ aci_password }}'
    validate_certs: no
    path: /api/mo/uni/tn-[Sales].json
    method: post
    content:
      fvTenant:
        attributes:
          name: Sales
          descr: Sales departement
  delegate_to: localhost

- name: Add a tenant using a JSON string
  aci_rest:
    hostname: '{{ inventory_hostname }}'
    username: '{{ aci_username }}'
    password: '{{ aci_password }}'
    validate_certs: no
    path: /api/mo/uni/tn-[Sales].json
    method: post
    content: |
      {
        "fvTenant": {
          "attributes": {
            "name": "Sales",
            "descr": "Sales departement"
          }
        }
      }
  delegate_to: localhost

- name: Add a tenant using an XML string
  aci_rest:
    hostname: '{{ inventory_hostname }}'
    username: '{{ aci_username }}'
    password: '{{ aci_password }}'
    validate_certs: no
    path: /api/mo/uni/tn-[Sales].xml
    method: post
    content: |
      <fvTenant name="Sales" descr="Sales departement"/>
  delegate_to: localhost

- name: Get tenants
  aci_rest:
    hostname: '{{ inventory_hostname }}'
    username: '{{ aci_username }}'
    password: '{{ aci_password }}'
    method: get
    path: /api/node/class/fvTenant.json
  delegate_to: localhost

- name: Configure contracts
  aci_rest:
    hostname: '{{ inventory_hostname }}'
    username: '{{ aci_username }}'
    password: '{{ aci_password }}'
    method: post
    path: /api/mo/uni.xml
    src: /home/cisco/ansible/aci/configs/contract_config.xml
  delegate_to: localhost

- name: Register leaves and spines
  aci_rest:
    hostname: '{{ inventory_hostname }}'
    username: '{{ aci_username }}'
    password: '{{ aci_password }}'
    validate_certs: no
    method: post
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
payload:
  description: The (templated) payload send to the APIC REST API (xml or json)
  returned: always
  type: string
  sample: '<foo bar="boo"/>'
raw:
  description: The raw output returned by the APIC REST API (xml or json)
  returned: parse error
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
  type: string
  sample: '0'
url:
  description: URL used for APIC REST call
  returned: success
  type: string
  sample: https://1.2.3.4/api/mo/uni/tn-[Dag].json?rsp-subtree=modified
'''

import json
import os

try:
    from ansible.module_utils.six.moves.urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
    HAS_URLPARSE = True
except:
    HAS_URLPARSE = False

# Optional, only used for XML payload
try:
    import lxml.etree
    assert lxml.etree  # silence pyflakes
    HAS_LXML_ETREE = True
except ImportError:
    HAS_LXML_ETREE = False

# Optional, only used for XML payload
try:
    from xmljson import cobra
    assert cobra  # silence pyflakes
    HAS_XMLJSON_COBRA = True
except ImportError:
    HAS_XMLJSON_COBRA = False

# Optional, only used for YAML validation
try:
    import yaml
    HAS_YAML = True
except:
    HAS_YAML = False

from ansible.module_utils.aci import ACIModule, aci_argument_spec, aci_response_json, aci_response_xml
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_text


def update_qsl(url, params):
    ''' Add or update a URL query string '''

    if HAS_URLPARSE:
        url_parts = list(urlparse(url))
        query = dict(parse_qsl(url_parts[4]))
        query.update(params)
        url_parts[4] = urlencode(query)
        return urlunparse(url_parts)
    elif '?' in url:
        return url + '&' + '&'.join(['%s=%s' % (k, v) for k, v in params.items()])
    else:
        return url + '?' + '&'.join(['%s=%s' % (k, v) for k, v in params.items()])


def aci_changed(d):
    ''' Check ACI response for changes '''

    if isinstance(d, dict):
        for k, v in d.items():
            if k == 'status' and v in ('created', 'modified', 'deleted'):
                return True
            elif aci_changed(v) is True:
                return True
    elif isinstance(d, list):
        for i in d:
            if aci_changed(i) is True:
                return True

    return False


def aci_response(result, rawoutput, rest_type='xml'):
    ''' Handle APIC response output '''

    if rest_type == 'json':
        aci_response_json(result, rawoutput)
    else:
        aci_response_xml(result, rawoutput)

    # Use APICs built-in idempotency
    if HAS_URLPARSE:
        result['changed'] = aci_changed(result)


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        path=dict(type='str', required=True, aliases=['uri']),
        method=dict(type='str', default='get', choices=['delete', 'get', 'post'], aliases=['action']),
        src=dict(type='path', aliases=['config_file']),
        content=dict(type='raw'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[['content', 'src']],
    )

    path = module.params['path']
    content = module.params['content']
    src = module.params['src']

    method = module.params['method']
    timeout = module.params['timeout']

    # Report missing file
    file_exists = False
    if src:
        if os.path.isfile(src):
            file_exists = True
        else:
            module.fail_json(msg="Cannot find/access src '%s'" % src)

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

    aci = ACIModule(module)

    # We include the payload as it may be templated
    payload = content
    if file_exists:
        with open(src, 'r') as config_object:
            # TODO: Would be nice to template this, requires action-plugin
            payload = config_object.read()

    # Validate content
    if rest_type == 'json':
        if content and isinstance(content, dict):
            # Validate inline YAML/JSON
            payload = json.dumps(payload)
        elif payload and isinstance(payload, str) and HAS_YAML:
            try:
                # Validate YAML/JSON string
                payload = json.dumps(yaml.load(payload))
            except Exception as e:
                module.fail_json(msg='Failed to parse provided JSON/YAML content: %s' % to_text(e), exception=to_text(e), payload=payload)
    elif rest_type == 'xml' and HAS_LXML_ETREE:
        if content and isinstance(content, dict) and HAS_XMLJSON_COBRA:
            # Validate inline YAML/JSON
            # FIXME: Converting from a dictionary to XML is unsupported at this time
            # payload = etree.tostring(payload)
            pass
        elif payload and isinstance(payload, str):
            try:
                # Validate XML string
                payload = lxml.etree.tostring(lxml.etree.fromstring(payload))
            except Exception as e:
                module.fail_json(msg='Failed to parse provided XML content: %s' % to_text(e), payload=payload)

    # Perform actual request using auth cookie (Same as aci_request,but also supports XML)
    url = '%(protocol)s://%(hostname)s/' % aci.params + path.lstrip('/')
    if method != 'get':
        url = update_qsl(url, {'rsp-subtree': 'modified'})
    aci.result['url'] = url

    resp, info = fetch_url(module, url, data=payload, method=method.upper(), timeout=timeout, headers=aci.headers)
    aci.result['response'] = info['msg']
    aci.result['status'] = info['status']

    # Report failure
    if info['status'] != 200:
        try:
            aci_response(aci.result, info['body'], rest_type)
            module.fail_json(msg='Request failed: %(error_code)s %(error_text)s' % aci.result, payload=payload, **aci.result)
        except KeyError:
            module.fail_json(msg='Request failed for %(url)s. %(msg)s' % info, payload=payload, **aci.result)

    aci_response(aci.result, resp.read(), rest_type)

    # Report success
    module.exit_json(**aci.result)


if __name__ == '__main__':
    main()
