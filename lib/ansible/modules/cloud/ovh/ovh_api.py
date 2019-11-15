#!/usr/bin/python

# Copyright: (c) 2019, OVH SAS <opensource@ovh.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovh_api
short_description: Interacts with OVH API
description:
    - Interacts with OVH (French European hosting provider) APIv6 and support
        the specific authentication and hearders
version_added: "2.11"
author: Yoann LAMOUREUX (@YoannAtOVH)
notes:
    - Uses the python OVH Api U(https://github.com/ovh/python-ovh).
      You have to create an application (a key and secret) with a consummer
      key as described into U(https://docs.ovh.com/gb/en/customer/first-steps-with-ovh-api/)
requirements:
    - ovh >  0.3.5
options:
    uri:
        required: true
        description:
            - Uniform Resource Identifier of the request
    method:
        default: GET
        choices: ['GET', 'POST', 'PUT', 'DELETE']
        description:
            - The HTTP method of the request
    endpoint:
        required: true
        description:
            - The endpoint to use ( for instance ovh-eu)
    application_key:
        required: true
        description:
            - The applicationKey to use
    application_secret:
        required: true
        description:
            - The application secret to use
    consumer_key:
        required: true
        description:
            - The consumer key to use
    timeout:
        default: 120
        description:
            - The timeout in seconds used to wait for a task to be
              completed.
'''

EXAMPLES = '''
# Get you personnal informations
- ovh_api:
    uri: "/me"
    method: "GET"
    endpoint: "ovh-eu"
    application_key: "yourkey"
    application_secret: "yoursecret"
    consumer_key: "yourconsumerkey"

# Get list of all installationTemplate of your account
- ovh_api:
    uri: "/me/installationTemplate"
    method: "GET"
    endpoint: "ovh-eu"
    application_key: "yourkey"
    application_secret: "yoursecret"
    consumer_key: "yourconsumerkey"
  register: installationTemplate

# Change default language of a installationTemplate
- ovh_api:
    uri: "/me/installationTemplate/{{ id }}"
    method: "PUT"
    body:
      defaultLanguage: "{{ lang }}"
    endpoint: "ovh-eu"
    application_key: "yourkey"
    application_secret: "yoursecret"
    consumer_key: "yourconsumerkey"
  vars:
    id: "your_template_id"
    lang: "en"

# Delete all installationTemplate with OLD in item id
-  ovh_api:
    uri: "/me/installationTemplate/{{ item }}"
    method: "DELETE"
    endpoint: "ovh-eu"
    application_key: "yourkey"
    application_secret: "yoursecret"
    consumer_key: "yourconsumerkey"
  when: item.find("OLD") != -1
  loop: "{{ result.json }}"
'''

RETURN = '''
json:
    description: The HTTP response body of the request
    returned: always
    type: json
    sample: ["Template-2"]
query_id:
    description: The API query ID of the request
    returned: on failure
    type: str
    sample: "EU.ext-0.5d766c5c.20806.666a83a8-001e-beef-85f6-0ef99938b1f2"
'''

try:
    import ovh
    import ovh.exceptions
    from ovh.exceptions import APIError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False

from ansible.module_utils.basic import AnsibleModule

def getovhclient(ansibleModule):
    endpoint = ansibleModule.params.get('endpoint')
    application_key = ansibleModule.params.get('application_key')
    application_secret = ansibleModule.params.get('application_secret')
    consumer_key = ansibleModule.params.get('consumer_key')

    return ovh.Client(
        endpoint=endpoint,
        application_key=application_key,
        application_secret=application_secret,
        consumer_key=consumer_key
    )

def main():
    module_args = dict(
        uri=dict(required=True),
        method=dict(default='GET',
                    choices=['GET', 'POST', 'PUT', 'DELETE']),
        endpoint=dict(required=True),
        body=dict(type='dict'),
        application_key=dict(required=True, no_log=True),
        application_secret=dict(required=True, no_log=True),
        consumer_key=dict(required=True, no_log=True),
        timeout=dict(default=120, type='int')
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False
    )

    if not HAS_OVH:
        module.fail_json(msg='ovh-api python module is required to run this ' +
                         'module ')

    if module.check_mode:
        module.exit_json(**result)

    # Get parameters
    uri = module.params.get('uri')
    method = module.params.get('method').upper()
    body = module.params.get('body')

    # Connect to OVH API
    client = getovhclient(module)

    uresp = {}

    try:
        if method == 'GET':
            uresp = client.get(uri)
            moduleChanged = False
        elif method == 'POST':
            uresp = client.post(uri, **body)
            moduleChanged = True
        elif method == 'PUT':
            uresp = client.put(uri, **body)
            moduleChanged = True
        elif method == 'DELETE':
            uresp = client.delete(uri)
            moduleChanged = True
        else:
            module.fail_json(msg='Unknow API Call check methode')
    except APIError as apierror:
        module.fail_json(
            msg='Unable to call OVH api check application key, secret, '
                'consumerkey and parameters. '
                'Error returned by OVH api was : {0}'.format(apierror),
            json=None,
            query_id=apierror.query_id)

    result['json'] = uresp
    result['changed'] = moduleChanged
    module.exit_json(**result)

if __name__ == '__main__':
    main()
