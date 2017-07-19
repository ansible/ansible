#!/usr/bin/python
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
#

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_tenant
short_description: Manage tenants on Cisco ACI fabrics
description:
- Manage tenants on a Cisco ACI fabric.
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
options:
  method:
    description:
    - The HTTP method of the request.
    - Using C(delete) is typically used for deleting objects.
    - Using C(get) is typically used for querying objects.
    - Using C(post) is typically used for modifying objects.
    required: true
    default: get
    choices: [ delete, get, post ]
    aliases: [ action ]
  tenant_name:
    description:
    - The name of the tenant.
    required: yes
  descr:
    description:
    - Description for the AEP.
extends_documentation_fragment: aci
'''

EXAMPLES = '''
- name: Add a new tenant
  aci_tenant:
    hostname: acme-apic-1
    username: admin
    password: SomeSecretPassword
    tenant_name: production
    descr: Name of the production tenant
    state: present
'''

RETURN = r'''
status:
  description: The status code of the http request
  returned: upon making a successful GET, POST or DELETE request to the APIC
  type: int
  sample: 200
response:
  description: Response text returned by APIC
  returned: when a HTTP request has been made to APIC
  type: string
  sample: '{"totalCount":"0","imdata":[]}'
'''

import json

# from ansible.module_utils.aci import aci_argument_spec, aci_login, aci_response
from ansible.module_utils.basic import AnsibleModule, get_exception
from ansible.module_utils.urls import fetch_url

aci_argument_spec = dict(
    hostname=dict(type='str', required=True, aliases=['host']),
    username=dict(type='str', default='admin', aliases=['user']),
    password=dict(type='str', required=True, no_log=True),
    protocol=dict(type='str'),  # Deprecated in v2.8
    timeout=dict(type='int', default=30),
    use_ssl=dict(type='bool', default=True),
    validate_certs=dict(type='bool', default=True),
)


def aci_login(module, result=dict()):
    ''' Log in to APIC '''

    # Set protocol based on use_ssl parameter
    if module.params['protocol'] is None:
        module.params['protocol'] = 'https' if module.params.get('use_ssl', True) else 'http'

    # Perform login request
    url = '%(protocol)s://%(hostname)s/api/aaaLogin.json' % module.params
    data = {'aaaUser': {'attributes': {'name': module.params['username'], 'pwd': module.params['password']}}}
    resp, auth = fetch_url(module, url, data=json.dumps(data), method="POST", timeout=module.params['timeout'])

    # Handle APIC response
    if auth['status'] != 200:
        try:
            result.update(aci_response(auth['body'], 'json'))
            result['msg'] = 'Authentication failed: %(error_code)s %(error_text)s' % result
        except KeyError:
            result['msg'] = '%(msg)s for %(url)s' % auth
        result['response'] = auth['msg']
        result['status'] = auth['status']
        module.fail_json(**result)

    return resp


def aci_response(rawoutput):
    ''' Handle APIC response output '''
    result = dict()

    # Use APIC response as module output
    try:
        result = json.loads(rawoutput)
    except:
        e = get_exception()
        # Expose RAW output for troubleshooting
        result['error_code'] = -1
        result['error_text'] = "Unable to parse output as JSON, see 'raw' output. %s" % e
        result['raw'] = rawoutput
        return result

    # Handle possible APIC error information
    try:
        result['error_code'] = result['imdata'][0]['error']['attributes']['code']
        result['error_text'] = result['imdata'][0]['error']['attributes']['text']
    except KeyError:
        result['error_code'] = 0
        result['error_text'] = 'Success'

    return result


def main():
    argument_spec = dict(
        # TODO: We should use 'state: absent' or 'state: present', not low-level HTTP requests
        method=dict(type='str', default='get', choices=['delete', 'get', 'post'], aliases=['action']),
        tenant_name=dict(type='str', aliases=['name']),
        description=dict(type='str', aliases=['descr']),
    )

    argument_spec.update(aci_argument_spec)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    hostname = module.params['hostname']
    username = module.params['username']
    password = module.params['password']

    # FIXME: This should not be needed
    action = module.params['action']
    name = module.params['tenant_name']
    description = module.params['description']

    protocol = module.params['protocol']
    use_ssl = module.params['use_ssl']
    method = module.params['method']
    timeout = module.params['timeout']

    result = dict(
        changed=False,
    )

    paths = dict(
        delete='api/mo/uni/tn-%(tenant_name)s.json' % module.params,
        get='api/node/class/fvTenant.json',
        post='api/mo/uni/tn-%(tenant_name)s.json' % module.params,
    )

    # Config payload to enable the physical interface
    config_data = {'fvTenant': {'attributes': {'name': tenant_name, 'descr': description}}}
    result['payload'] = json.dumps(config_data)

    # Set protocol for further use
    if protocol is None:
        protocol = 'https' if use_ssl else 'http'
    else:
        module.deprecate("Parameter 'protocol' is deprecated, please use 'use_ssl' instead.", 2.8)

    # Perform login first
    auth = aci_login(module, result)

    # TODO: To test for idempotency we should do a get-request before and after and compare output
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
    url = '%s://%s/%s' % (protocol, hostname, paths[method].lstrip('/'))
    headers = dict(Cookie=auth.headers['Set-Cookie'])

    resp, info = fetch_url(module, url, data=result['payload'], method=method.upper(), timeout=timeout, headers=headers)
    result['response'] = info['msg']
    result['status'] = info['status']

    # Report failure
    if info['status'] != 200:
        try:
            result.update(aci_response(info['body']))
            result['msg'] = 'Task failed: %(error_code)s %(error_text)s' % result
        except KeyError:
            result['msg'] = '%(msg)s for %(url)s' % info
        module.fail_json(**result)

    # Report success
    result.update(aci_response(resp.read(), rest_type))
    module.exit_json(**result)

if __name__ == "__main__":
    main()
