#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, NT1 project (https://neic.no/nt1/)
# GNU General Public license v3.0+ (see COPYING or https://www.gnu.org/license/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: dcache_pool

short_description: dCache pool mode setup through REST interface

version_added: "2.8"

description:
    - "Sets the mode of the dCache pools. Requires admin privileges
       for the account that executes commands."

options:
    url:
        description:
            - URL of the dCache central service
        required: true

    port:
        description:
            - Port number of the dCache central service
        default: 3880

    username:
        description:
            - Name of the account with administrative privileges
        required: true

    password:
        description:
            - Password for the account with administrative privileges
        required: true

    pool_name:
        description:
            - The name of the pool to manipulate
        required: true

    set_read_only:
        description:
            - Specifies if the pool should be made read only
        default: false
        type: bool

    set_resilient:
        description:
            - Specifies if the pool should be made resilient
        default: true
        type: bool

requirements:
    - "requests >= 2.21.0"

notes:
    - "Supports check mode"
    - "If both set_read_only and set_resilient are omitted, the pool will be
       reset to the default mode (not readonly, resilient)"
    - "dCache REST interface has some delays before the change of the mode
        becomes visible. Do not run the module several times on the same pool
        without pauses, it might cause unpredictable results."
    - "The previous item also makes it hard to return the new pool mode after
        the execution. The module therefore only returns if there were changes
        to its original mode or not"
    - "The module expects to find CA certificates under /etc/grid-security/certificates.
        Will fail if they are not there."

author:
    - Dmytro Karpenko (@dmykarp)
'''

EXAMPLES = '''
# Set the pool to the default mode (not readonly, resilient)
- name: Put the pool in production
  dcache_pool:
    url: https://dcache.acme.org
    username: admin
    port: 3880
    password: "{{ user_input_password }}"
    pool_name: pool_001
    set_read_only: no
    set_resilient: yes
'''

RETURN = ''' # '''

from ansible.module_utils.basic import AnsibleModule
from requests.auth import HTTPBasicAuth
from requests.exceptions import SSLError, ConnectionError
import json

try:
    import requests
    HAS_REQUESTS=True
except:
    HAS_REQUESTS=False

def decode_current_state(current_pool_state):

    current_read_only = False
    current_resilience = True
    if 'disabled' in current_pool_state:
        current_read_only = True
    if 'noresilience' in current_pool_state:
        current_resilience = False
    return current_read_only, current_resilience


def compose_patch_body(set_read_only, set_resilient):

    # Booleans have to become strings, REST API only accepts strings for now
    patch_body = dict()
    patch_body['rdonly'] = str(set_read_only)
    if not set_read_only:
        # Readonly pools are always non-resilient
        # We care about set_resilient only for non-readonly pools
        patch_body['resilience'] = str(set_resilient)

    return json.dumps(patch_body)


class dCacheREST(object):

    api_url_part = '/api/v1'
    admin_role = '#admin'
    pools_url = '/pools/'
    usage_url = '/usage'
    mode_url = '/mode'
    # A traditional path to CA certs on the machines that manipulate dcache
    CA_path = '/etc/grid-security/certificates'

    def __init__(self, module):
        mparams = module.params
        self.pool_name = mparams['pool_name']
        self.basic_url = mparams['url'] + ':' + mparams['port'] + dCacheREST.api_url_part
        self.pool_usage_url = self.basic_url + dCacheREST.pools_url + self.pool_name + dCacheREST.usage_url
        self.REST_auth = HTTPBasicAuth(mparams['username'] + dCacheREST.admin_role, mparams['password'])
        self._module = module

    def handle_error_code(self, error_code):
        # Errors from PATCH to pools/<pool_name>/usage/mode
        if error_code == 400:
            error_msg = "Bad request to %s" % self.basic_url
        elif error_code == 403:
            error_msg = "The pool mode change is only permitted to the admin user"
        elif error_code == 500:
            error_msg = "Internal server error on %s" % self.basic_url
        else:
            # Should never enter this branch
            error_msg = "Unknown error happened"
        self._module.fail_json(failed=True, msg=error_msg)

    def get_current_pool_mode(self):
        try:
            # It can only return success, in case of failure the exception is thrown
            res = requests.get(self.pool_usage_url, verify=dCacheREST.CA_path, auth=self.REST_auth)
        except SSLError as e:
            self._module.fail_json(failed=True, msg="Cannot verify the certificate for %s." % self.basic_url)
        except ConnectionError as e:
            self._module.fail_json(failed=True, msg="Cannot connect to %s." % self.basic_url)

        # If the pool does not exist or is down, the status code is still success,
        # but the result dict is empty.
        if res.json():
            return res.json()['poolData']['detailsData']['poolMode']
        else:
            self._module.fail_json(failed=True, msg="Cannot connect to pool %s." % self.pool_name)

    def modify_pool_mode(self, payload):
        self.pool_mode_url = self.pool_usage_url + dCacheREST.mode_url
        try:
            res = requests.patch(self.pool_mode_url, data=payload, verify=dCacheREST.CA_path, auth=self.REST_auth)
            if res.status_code != requests.codes.ok:
                self.handle_error_code(res.status_code)
        except SSLError as e:
            self._module.fail_json(failed=True, msg="Cannot verify the certificate for %s." % self.basic_url)
        except ConnectionError as e:
            self._module.fail_json(failed=True, msg="Cannot connect to %s." % self.basic_url)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(required=True),
            port=dict(required=False, default='3880'),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            pool_name=dict(required=True),
            set_read_only=dict(required=False, default=False, type='bool'),
            set_resilient=dict(required=False, default=True, type='bool')
        ),
        supports_check_mode=True
    )

    if not HAS_REQUESTS:
        module.fail_json(failed=True, msg="requests module is required")

    params = module.params

    dCacheRESTComm = dCacheREST(module)

    current_pool_mode = dCacheRESTComm.get_current_pool_mode()

    current_read_only, current_resilience = decode_current_state(current_pool_mode)

    if (current_read_only != params['set_read_only']):
        is_changed = True
    # If the pool is readonly, no change to resilience is possible
    elif not current_read_only and (current_resilience != params['set_resilient']):
        is_changed = True
    else:
        is_changed = False

    if is_changed and not module.check_mode:
        patch_data = compose_patch_body(params['set_read_only'], params['set_resilient'])
        dCacheRESTComm.modify_pool_mode(patch_data)

    module.exit_json(changed=is_changed)


if __name__ == '__main__':
    main()
