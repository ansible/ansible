#!/usr/bin/python
# -*- coding: utf-8 -*-

#  Copyright (c) 2017 Citrix Systems
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: netscaler_nitro_request
short_description: Issue Nitro API requests to a Netscaler instance.
description:
    - Issue Nitro API requests to a Netscaler instance.
    - This is intended to be a short hand for using the uri Ansible module to issue the raw HTTP requests directly.
    - It provides consistent return values and has no other dependencies apart from the base Ansible runtime environment.
    - This module is intended to run either on the Ansible control node or a bastion (jumpserver) with access to the actual Netscaler instance


version_added: "2.5.0"

author: George Nikolopoulos (@giorgos-nikolopoulos)

options:

    nsip:
        description:
            - The IP address of the Netscaler or MAS instance where the Nitro API calls will be made.
            - "The port can be specified with the colon C(:). E.g. C(192.168.1.1:555)."

    nitro_user:
        description:
            - The username with which to authenticate to the Netscaler node.
        required: true

    nitro_pass:
        description:
            - The password with which to authenticate to the Netscaler node.
        required: true

    nitro_protocol:
        choices: [ 'http', 'https' ]
        default: http
        description:
            - Which protocol to use when accessing the Nitro API objects.

    validate_certs:
        description:
            - If C(no), SSL certificates will not be validated. This should only be used on personally controlled sites using self-signed certificates.
        default: 'yes'
        type: bool

    nitro_auth_token:
        description:
            - The authentication token provided by the C(mas_login) operation. It is required when issuing Nitro API calls through a MAS proxy.

    resource:
        description:
            - The type of resource we are operating on.
            - It is required for all I(operation) values except C(mas_login) and C(save_config).

    name:
        description:
            - The name of the resource we are operating on.
            - "It is required for the following I(operation) values: C(update), C(get), C(delete)."

    attributes:
        description:
            - The attributes of the Nitro object we are operating on.
            - "It is required for the following I(operation) values: C(add), C(update), C(action)."

    args:
        description:
            - A dictionary which defines the key arguments by which we will select the Nitro object to operate on.
            - "It is required for the following I(operation) values: C(get_by_args), C('delete_by_args')."

    filter:
        description:
            - A dictionary which defines the filter with which to refine the Nitro objects returned by the C(get_filtered) I(operation).

    operation:
        description:
            - Define the Nitro operation that we want to perform.
        choices:
            - add
            - update
            - get
            - get_by_args
            - get_filtered
            - get_all
            - delete
            - delete_by_args
            - count
            - mas_login
            - save_config
            - action

    expected_nitro_errorcode:
        description:
            - A list of numeric values that signify that the operation was successful.
        default: [0]
        required: true

    action:
        description:
            - The action to perform when the I(operation) value is set to C(action).
            - Some common values for this parameter are C(enable), C(disable), C(rename).

    instance_ip:
        description:
            - The IP address of the target Netscaler instance when issuing a Nitro request through a MAS proxy.

    instance_name:
        description:
            - The name of the target Netscaler instance when issuing a Nitro request through a MAS proxy.

    instance_id:
        description:
            - The id of the target Netscaler instance when issuing a Nitro request through a MAS proxy.
'''

EXAMPLES = '''
- name: Add a server
  delegate_to: localhost
  netscaler_nitro_request:
    nsip: "{{ nsip }}"
    nitro_user: "{{ nitro_user }}"
    nitro_pass: "{{ nitro_pass }}"
    operation: add
    resource: server
    name: test-server-1
    attributes:
      name: test-server-1
      ipaddress: 192.168.1.1

- name: Update server
  delegate_to: localhost
  netscaler_nitro_request:
    nsip: "{{ nsip }}"
    nitro_user: "{{ nitro_user }}"
    nitro_pass: "{{ nitro_pass }}"
    operation: update
    resource: server
    name: test-server-1
    attributes:
      name: test-server-1
      ipaddress: 192.168.1.2

- name: Get server
  delegate_to: localhost
  register: result
  netscaler_nitro_request:
    nsip: "{{ nsip }}"
    nitro_user: "{{ nitro_user }}"
    nitro_pass: "{{ nitro_pass }}"
    operation: get
    resource: server
    name: test-server-1

- name: Delete server
  delegate_to: localhost
  register: result
  netscaler_nitro_request:
    nsip: "{{ nsip }}"
    nitro_user: "{{ nitro_user }}"
    nitro_pass: "{{ nitro_pass }}"
    operation: delete
    resource: server
    name: test-server-1

- name: Rename server
  delegate_to: localhost
  netscaler_nitro_request:
    nsip: "{{ nsip }}"
    nitro_user: "{{ nitro_user }}"
    nitro_pass: "{{ nitro_pass }}"
    operation: action
    action: rename
    resource: server
    attributes:
      name: test-server-1
      newname: test-server-2

- name: Get server by args
  delegate_to: localhost
  register: result
  netscaler_nitro_request:
    nsip: "{{ nsip }}"
    nitro_user: "{{ nitro_user }}"
    nitro_pass: "{{ nitro_pass }}"
    operation: get_by_args
    resource: server
    args:
      name: test-server-1

- name: Get server by filter
  delegate_to: localhost
  register: result
  netscaler_nitro_request:
    nsip: "{{ nsip }}"
    nitro_user: "{{ nitro_user }}"
    nitro_pass: "{{ nitro_pass }}"
    operation: get_filtered
    resource: server
    filter:
      ipaddress: 192.168.1.2

# Doing a NITRO request through MAS.
# Requires to have an authentication token from the mas_login and used as the nitro_auth_token parameter
# Also nsip is the MAS address and the target Netscaler IP must be defined with instance_ip
# The rest of the task arguments remain the same as when issuing the NITRO request directly to a Netscaler instance.

- name: Do mas login
  delegate_to: localhost
  register: login_result
  netscaler_nitro_request:
    nsip: "{{ mas_ip }}"
    nitro_user: "{{ nitro_user }}"
    nitro_pass: "{{ nitro_pass }}"
    operation: mas_login

- name: Add resource through MAS proxy
  delegate_to: localhost
  netscaler_nitro_request:
    nsip: "{{ mas_ip }}"
    nitro_auth_token: "{{ login_result.nitro_auth_token }}"
    instance_ip: "{{ nsip }}"
    operation: add
    resource: server
    name: test-server-1
    attributes:
      name: test-server-1
      ipaddress: 192.168.1.7
'''

RETURN = '''
nitro_errorcode:
    description: A numeric value containing the return code of the NITRO operation. When 0 the operation is succesful. Any non zero value indicates an error.
    returned: always
    type: int
    sample: 0

nitro_message:
    description: A string containing a human readable explanation for the NITRO operation result.
    returned: always
    type: str
    sample: Success

nitro_severity:
    description: A string describing the severity of the NITRO operation error or NONE.
    returned: always
    type: str
    sample: NONE

http_response_data:
    description: A dictionary that contains all the HTTP response's data.
    returned: always
    type: dict
    sample: "status: 200"

http_response_body:
    description: A string with the actual HTTP response body content if existent. If there is no HTTP response body it is an empty string.
    returned: always
    type: str
    sample: "{ errorcode: 0, message: Done, severity: NONE }"

nitro_object:
    description: The object returned from the NITRO operation. This is applicable to the various get operations which return an object.
    returned: when applicable
    type: list
    sample:
        -
            ipaddress: "192.168.1.8"
            ipv6address: "NO"
            maxbandwidth: "0"
            name: "test-server-1"
            port: 0
            sp: "OFF"
            state: "ENABLED"

nitro_auth_token:
    description: The token returned by the C(mas_login) operation when succesful.
    returned: when applicable
    type: str
    sample: "##E8D7D74DDBD907EE579E8BB8FF4529655F22227C1C82A34BFC93C9539D66"
'''


from ansible.module_utils.urls import fetch_url
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.basic import AnsibleModule
import codecs


class NitroAPICaller(object):

    _argument_spec = dict(
        nsip=dict(
            fallback=(env_fallback, ['NETSCALER_NSIP']),
        ),
        nitro_user=dict(
            fallback=(env_fallback, ['NETSCALER_NITRO_USER']),
        ),
        nitro_pass=dict(
            fallback=(env_fallback, ['NETSCALER_NITRO_PASS']),
            no_log=True
        ),
        nitro_protocol=dict(
            choices=['http', 'https'],
            fallback=(env_fallback, ['NETSCALER_NITRO_PROTOCOL']),
            default='http'
        ),
        validate_certs=dict(
            default=True,
            type='bool'
        ),
        nitro_auth_token=dict(
            type='str',
            no_log=True
        ),
        resource=dict(type='str'),
        name=dict(type='str'),
        attributes=dict(type='dict'),

        args=dict(type='dict'),
        filter=dict(type='dict'),

        operation=dict(
            type='str',
            required=True,
            choices=[
                'add',
                'update',
                'get',
                'get_by_args',
                'get_filtered',
                'get_all',
                'delete',
                'delete_by_args',
                'count',

                'mas_login',

                # Actions
                'save_config',

                # Generic action handler
                'action',
            ]
        ),
        expected_nitro_errorcode=dict(
            type='list',
            default=[0],
        ),
        action=dict(type='str'),
        instance_ip=dict(type='str'),
        instance_name=dict(type='str'),
        instance_id=dict(type='str'),
    )

    def __init__(self):

        self._module = AnsibleModule(
            argument_spec=self._argument_spec,
            supports_check_mode=False,
        )

        self._module_result = dict(
            failed=False,
        )

        # Prepare the http headers according to module arguments
        self._headers = {}
        self._headers['Content-Type'] = 'application/json'

        # Check for conflicting authentication methods
        have_token = self._module.params['nitro_auth_token'] is not None
        have_userpass = None not in (self._module.params['nitro_user'], self._module.params['nitro_pass'])
        login_operation = self._module.params['operation'] == 'mas_login'

        if have_token and have_userpass:
            self.fail_module(msg='Cannot define both authentication token and username/password')

        if have_token:
            self._headers['Cookie'] = "NITRO_AUTH_TOKEN=%s" % self._module.params['nitro_auth_token']

        if have_userpass and not login_operation:
            self._headers['X-NITRO-USER'] = self._module.params['nitro_user']
            self._headers['X-NITRO-PASS'] = self._module.params['nitro_pass']

        # Do header manipulation when doing a MAS proxy call
        if self._module.params['instance_ip'] is not None:
            self._headers['_MPS_API_PROXY_MANAGED_INSTANCE_IP'] = self._module.params['instance_ip']
        elif self._module.params['instance_name'] is not None:
            self._headers['_MPS_API_PROXY_MANAGED_INSTANCE_NAME'] = self._module.params['instance_name']
        elif self._module.params['instance_id'] is not None:
            self._headers['_MPS_API_PROXY_MANAGED_INSTANCE_ID'] = self._module.params['instance_id']

    def edit_response_data(self, r, info, result, success_status):
        # Search for body in both http body and http data
        if r is not None:
            result['http_response_body'] = codecs.decode(r.read(), 'utf-8')
        elif 'body' in info:
            result['http_response_body'] = codecs.decode(info['body'], 'utf-8')
            del info['body']
        else:
            result['http_response_body'] = ''

        result['http_response_data'] = info

        # Update the nitro_* parameters according to expected success_status
        # Use explicit return values from http response or deduce from http status code

        # Nitro return code in http data
        result['nitro_errorcode'] = None
        result['nitro_message'] = None
        result['nitro_severity'] = None

        if result['http_response_body'] != '':
            try:
                data = self._module.from_json(result['http_response_body'])
            except ValueError:
                data = {}
            result['nitro_errorcode'] = data.get('errorcode')
            result['nitro_message'] = data.get('message')
            result['nitro_severity'] = data.get('severity')

        # If we do not have the nitro errorcode from body deduce it from the http status
        if result['nitro_errorcode'] is None:
            # HTTP status failed
            if result['http_response_data'].get('status') != success_status:
                result['nitro_errorcode'] = -1
                result['nitro_message'] = result['http_response_data'].get('msg', 'HTTP status %s' % result['http_response_data']['status'])
                result['nitro_severity'] = 'ERROR'
            # HTTP status succeeded
            else:
                result['nitro_errorcode'] = 0
                result['nitro_message'] = 'Success'
                result['nitro_severity'] = 'NONE'

    def handle_get_return_object(self, result):
        result['nitro_object'] = []
        if result['nitro_errorcode'] == 0:
            if result['http_response_body'] != '':
                data = self._module.from_json(result['http_response_body'])
                if self._module.params['resource'] in data:
                    result['nitro_object'] = data[self._module.params['resource']]
        else:
            del result['nitro_object']

    def fail_module(self, msg, **kwargs):
        self._module_result['failed'] = True
        self._module_result['changed'] = False
        self._module_result.update(kwargs)
        self._module_result['msg'] = msg
        self._module.fail_json(**self._module_result)

    def main(self):
        if self._module.params['operation'] == 'add':
            result = self.add()

        if self._module.params['operation'] == 'update':
            result = self.update()

        if self._module.params['operation'] == 'delete':
            result = self.delete()

        if self._module.params['operation'] == 'delete_by_args':
            result = self.delete_by_args()

        if self._module.params['operation'] == 'get':
            result = self.get()

        if self._module.params['operation'] == 'get_by_args':
            result = self.get_by_args()

        if self._module.params['operation'] == 'get_filtered':
            result = self.get_filtered()

        if self._module.params['operation'] == 'get_all':
            result = self.get_all()

        if self._module.params['operation'] == 'count':
            result = self.count()

        if self._module.params['operation'] == 'mas_login':
            result = self.mas_login()

        if self._module.params['operation'] == 'action':
            result = self.action()

        if self._module.params['operation'] == 'save_config':
            result = self.save_config()

        if result['nitro_errorcode'] not in self._module.params['expected_nitro_errorcode']:
            self.fail_module(msg='NITRO Failure', **result)

        self._module_result.update(result)
        self._module.exit_json(**self._module_result)

    def exit_module(self):
        self._module.exit_json()

    def add(self):
        # Check if required attributes are present
        if self._module.params['resource'] is None:
            self.fail_module(msg='NITRO resource is undefined.')
        if self._module.params['attributes'] is None:
            self.fail_module(msg='NITRO resource attributes are undefined.')

        url = '%s://%s/nitro/v1/config/%s' % (
            self._module.params['nitro_protocol'],
            self._module.params['nsip'],
            self._module.params['resource'],
        )

        data = self._module.jsonify({self._module.params['resource']: self._module.params['attributes']})

        r, info = fetch_url(
            self._module,
            url=url,
            headers=self._headers,
            data=data,
            method='POST',
        )

        result = {}

        self.edit_response_data(r, info, result, success_status=201)

        if result['nitro_errorcode'] == 0:
            self._module_result['changed'] = True
        else:
            self._module_result['changed'] = False

        return result

    def update(self):
        # Check if required attributes are arguments present
        if self._module.params['resource'] is None:
            self.fail_module(msg='NITRO resource is undefined.')
        if self._module.params['name'] is None:
            self.fail_module(msg='NITRO resource name is undefined.')

        if self._module.params['attributes'] is None:
            self.fail_module(msg='NITRO resource attributes are undefined.')

        url = '%s://%s/nitro/v1/config/%s/%s' % (
            self._module.params['nitro_protocol'],
            self._module.params['nsip'],
            self._module.params['resource'],
            self._module.params['name'],
        )

        data = self._module.jsonify({self._module.params['resource']: self._module.params['attributes']})

        r, info = fetch_url(
            self._module,
            url=url,
            headers=self._headers,
            data=data,
            method='PUT',
        )

        result = {}
        self.edit_response_data(r, info, result, success_status=200)

        if result['nitro_errorcode'] == 0:
            self._module_result['changed'] = True
        else:
            self._module_result['changed'] = False

        return result

    def get(self):
        if self._module.params['resource'] is None:
            self.fail_module(msg='NITRO resource is undefined.')
        if self._module.params['name'] is None:
            self.fail_module(msg='NITRO resource name is undefined.')

        url = '%s://%s/nitro/v1/config/%s/%s' % (
            self._module.params['nitro_protocol'],
            self._module.params['nsip'],
            self._module.params['resource'],
            self._module.params['name'],
        )

        r, info = fetch_url(
            self._module,
            url=url,
            headers=self._headers,
            method='GET',
        )

        result = {}
        self.edit_response_data(r, info, result, success_status=200)

        self.handle_get_return_object(result)
        self._module_result['changed'] = False

        return result

    def get_by_args(self):
        if self._module.params['resource'] is None:
            self.fail_module(msg='NITRO resource is undefined.')

        if self._module.params['args'] is None:
            self.fail_module(msg='NITRO args is undefined.')

        url = '%s://%s/nitro/v1/config/%s' % (
            self._module.params['nitro_protocol'],
            self._module.params['nsip'],
            self._module.params['resource'],
        )

        args_dict = self._module.params['args']
        args = ','.join(['%s:%s' % (k, args_dict[k]) for k in args_dict])

        args = 'args=' + args

        url = '?'.join([url, args])

        r, info = fetch_url(
            self._module,
            url=url,
            headers=self._headers,
            method='GET',
        )
        result = {}
        self.edit_response_data(r, info, result, success_status=200)

        self.handle_get_return_object(result)
        self._module_result['changed'] = False

        return result

    def get_filtered(self):
        if self._module.params['resource'] is None:
            self.fail_module(msg='NITRO resource is undefined.')

        if self._module.params['filter'] is None:
            self.fail_module(msg='NITRO filter is undefined.')

        keys = list(self._module.params['filter'].keys())
        filter_key = keys[0]
        filter_value = self._module.params['filter'][filter_key]
        filter_str = '%s:%s' % (filter_key, filter_value)

        url = '%s://%s/nitro/v1/config/%s?filter=%s' % (
            self._module.params['nitro_protocol'],
            self._module.params['nsip'],
            self._module.params['resource'],
            filter_str,
        )

        r, info = fetch_url(
            self._module,
            url=url,
            headers=self._headers,
            method='GET',
        )

        result = {}
        self.edit_response_data(r, info, result, success_status=200)
        self.handle_get_return_object(result)
        self._module_result['changed'] = False

        return result

    def get_all(self):
        if self._module.params['resource'] is None:
            self.fail_module(msg='NITRO resource is undefined.')

        url = '%s://%s/nitro/v1/config/%s' % (
            self._module.params['nitro_protocol'],
            self._module.params['nsip'],
            self._module.params['resource'],
        )

        print('headers %s' % self._headers)
        r, info = fetch_url(
            self._module,
            url=url,
            headers=self._headers,
            method='GET',
        )

        result = {}
        self.edit_response_data(r, info, result, success_status=200)
        self.handle_get_return_object(result)
        self._module_result['changed'] = False

        return result

    def delete(self):
        if self._module.params['resource'] is None:
            self.fail_module(msg='NITRO resource is undefined.')

        if self._module.params['name'] is None:
            self.fail_module(msg='NITRO resource is undefined.')

        # Deletion by name takes precedence over deletion by attributes

        url = '%s://%s/nitro/v1/config/%s/%s' % (
            self._module.params['nitro_protocol'],
            self._module.params['nsip'],
            self._module.params['resource'],
            self._module.params['name'],
        )

        r, info = fetch_url(
            self._module,
            url=url,
            headers=self._headers,
            method='DELETE',
        )

        result = {}
        self.edit_response_data(r, info, result, success_status=200)

        if result['nitro_errorcode'] == 0:
            self._module_result['changed'] = True
        else:
            self._module_result['changed'] = False

        return result

    def delete_by_args(self):
        if self._module.params['resource'] is None:
            self.fail_module(msg='NITRO resource is undefined.')

        if self._module.params['args'] is None:
            self.fail_module(msg='NITRO args is undefined.')

        url = '%s://%s/nitro/v1/config/%s' % (
            self._module.params['nitro_protocol'],
            self._module.params['nsip'],
            self._module.params['resource'],
        )

        args_dict = self._module.params['args']
        args = ','.join(['%s:%s' % (k, args_dict[k]) for k in args_dict])

        args = 'args=' + args

        url = '?'.join([url, args])
        r, info = fetch_url(
            self._module,
            url=url,
            headers=self._headers,
            method='DELETE',
        )
        result = {}
        self.edit_response_data(r, info, result, success_status=200)

        if result['nitro_errorcode'] == 0:
            self._module_result['changed'] = True
        else:
            self._module_result['changed'] = False

        return result

    def count(self):
        if self._module.params['resource'] is None:
            self.fail_module(msg='NITRO resource is undefined.')

        url = '%s://%s/nitro/v1/config/%s?count=yes' % (
            self._module.params['nitro_protocol'],
            self._module.params['nsip'],
            self._module.params['resource'],
        )

        r, info = fetch_url(
            self._module,
            url=url,
            headers=self._headers,
            method='GET',
        )

        result = {}
        self.edit_response_data(r, info, result)

        if result['http_response_body'] != '':
            data = self._module.from_json(result['http_response_body'])

            result['nitro_errorcode'] = data['errorcode']
            result['nitro_message'] = data['message']
            result['nitro_severity'] = data['severity']
            if self._module.params['resource'] in data:
                result['nitro_count'] = data[self._module.params['resource']][0]['__count']

        self._module_result['changed'] = False

        return result

    def action(self):
        # Check if required attributes are present
        if self._module.params['resource'] is None:
            self.fail_module(msg='NITRO resource is undefined.')
        if self._module.params['attributes'] is None:
            self.fail_module(msg='NITRO resource attributes are undefined.')
        if self._module.params['action'] is None:
            self.fail_module(msg='NITRO action is undefined.')

        url = '%s://%s/nitro/v1/config/%s?action=%s' % (
            self._module.params['nitro_protocol'],
            self._module.params['nsip'],
            self._module.params['resource'],
            self._module.params['action'],
        )

        data = self._module.jsonify({self._module.params['resource']: self._module.params['attributes']})

        r, info = fetch_url(
            self._module,
            url=url,
            headers=self._headers,
            data=data,
            method='POST',
        )

        result = {}

        self.edit_response_data(r, info, result, success_status=200)

        if result['nitro_errorcode'] == 0:
            self._module_result['changed'] = True
        else:
            self._module_result['changed'] = False

        return result

    def mas_login(self):
        url = '%s://%s/nitro/v1/config/login' % (
            self._module.params['nitro_protocol'],
            self._module.params['nsip'],
        )

        login_credentials = {
            'login': {

                'username': self._module.params['nitro_user'],
                'password': self._module.params['nitro_pass'],
            }
        }

        data = 'object=\n%s' % self._module.jsonify(login_credentials)

        r, info = fetch_url(
            self._module,
            url=url,
            headers=self._headers,
            data=data,
            method='POST',
        )
        print(r, info)

        result = {}
        self.edit_response_data(r, info, result, success_status=200)

        if result['nitro_errorcode'] == 0:
            body_data = self._module.from_json(result['http_response_body'])
            result['nitro_auth_token'] = body_data['login'][0]['sessionid']

        self._module_result['changed'] = False

        return result

    def save_config(self):

        url = '%s://%s/nitro/v1/config/nsconfig?action=save' % (
            self._module.params['nitro_protocol'],
            self._module.params['nsip'],
        )

        data = self._module.jsonify(
            {
                'nsconfig': {},
            }
        )
        r, info = fetch_url(
            self._module,
            url=url,
            headers=self._headers,
            data=data,
            method='POST',
        )

        result = {}

        self.edit_response_data(r, info, result, success_status=200)
        self._module_result['changed'] = False

        return result


def main():

    nitro_api_caller = NitroAPICaller()
    nitro_api_caller.main()


if __name__ == '__main__':
    main()
