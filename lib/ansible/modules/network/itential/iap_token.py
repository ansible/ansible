#!/usr/bin/python

# Copyright: (c) 2018, Itential <opensource@itential.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: iap_token
version_added: "2.6"
author: "Itential (opensource@itential.com)"
requirements:
  - requests
short_description: Get token for the Itential Automation Platform
description:
  - Checks the connection to IAP and retrieves a login token.
options:
  iap_port:
    description:
      - Provide the port number for the Itential Automation Platform
    required: true
    default: null

  iap_fqdn:
    description:
      - Provide the fqdn for the Itential Automation Platform
    required: true
    default: null

  username:
    description:
      - Provide the username for the Itential Automation Platform
    required: true
    default: null

  password:
    description:
      - Provide the password for the Itential Automation Platform
    required: true
    default: null

  https:
    description:
      - The transport protocol is HyperText Transfer Protocol Secure (HTTPS) for the Itential Automation Platform
      - By default using http
    type: bool
    default: False

notes:
  - This module is under construction
'''

EXAMPLES = '''
- name: Get token for the Itential Automation Platform
  iap_token:
    iap_port: 3000
    iap_fqdn: localhost
    username: myusername
    password: mypass
  register: result

- debug: var=result.token
'''

RETURN = '''
token:
    description: The token acquired from the Itential Automation Platform
    type: str
    returned: always
'''

# Ansible imports
from ansible.module_utils.basic import AnsibleModule

# Standard library imports
import ansible.module_utils.urls
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        iap_port=dict(type='str', required=True),
        iap_fqdn=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True),
        https=(dict(type='bool', default=False))
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        token='',
        msg=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # manipulate or modify the state as needed
    # hit the target system and get the token

    # defaulting the value for transport_protocol to be : http
    transport_protocol = 'http'
    if module.params['https'] is True:
        transport_protocol = 'https'

    url = transport_protocol + "://" + module.params['iap_fqdn'] + ":" + module.params['iap_port'] + "/login"
    username = module.params['username']
    password = module.params['password']

    login = {
        "user": {
            "username": username,
            "password": password
        }
    }
    try:
        r = requests.post(url=url, json=login)
        r.raise_for_status()
        if r.status_code == 200:
            result['changed'] = True
            result['token'] = r.content
            result['msg'] = 'Token found'
    except requests.ConnectionError as err:
        module.fail_json(msg="Failed to connect to Itential Automation Platform : {} ".format(err), **result)
    except requests.exceptions.HTTPError as errh:
        module.fail_json(msg="Http Error: {} ".format(errh), **result)
    except requests.exceptions.Timeout as errt:
        module.fail_json(msg="Timeout Error: {} ".format(errt), **result)
    except requests.exceptions.RequestException as err:
        module.fail_json(msg="Something happened: {} ".format(err), **result)
    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
