#!/usr/bin/python
#
# (c) 2018, Jean-Philippe Evrard <jean-philippe@evrard.me>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
---
module: etcd3
short_description: "Set or delete key value pairs from an etcd3 cluster"
version_added: "2.5"
requirements:
  - etcd3
description:
   - Sets or deletes values in etcd3 cluster using its v3 api.
   - Needs python etcd3 lib to work.
options:
    key:
        description:
            - The key where the information is stored in the cluster.
        required: true
    value:
        description:
            - The information stored.
            - Required if C(state=present).
    host:
        description:
            - The IP address of the cluster.
        default: 'localhost'
    port:
        description:
            - The port number used to connect to the cluster.
        default: 2379
    state:
        description:
            - The state of the value for the key.
            - Can be present, absent or delete_range. If set to delete_range, the key is interpreted as a prefix and all keys with that prefix will be deleted.
        choices: [ present, absent, absent_prefix ]
        required: true
author:
    - Jean-Philippe Evrard (@evrardjp)
"""

EXAMPLES = """
# Store a value "bar" under the key "foo" for a cluster located at "http://localhost:2379"
- etcd3:
    key: "foo"
    value: "baz3"
    host: "localhost"
    port: 2379
    state: "present"

# Delete all keys beginning with "keys/foo" for a cluster installed on localhost
- etcd3:
    key: "keys/foo"
    state: absent_prefix
"""

RETURN = '''
key:
    description: The key that was queried
    returned: always
    type: str
old_value:
    description: The previous value in the cluster
    returned: always
    type: str
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
try:
    import etcd3
    etcd_found = True
except ImportError:
    etcd_found = False


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        key=dict(type='str', required=True),
        value=dict(type='str'),
        host=dict(type='str', default='localhost'),
        port=dict(type='int', default=2379),
        state=dict(type='str', required=True, choices=['present', 'absent', 'absent_prefix']),
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[["state", "present", ["value"]]]
    )

    result['key'] = module.params.get('key')

    if not etcd_found:
        module.fail_json(msg="The python etcd3 module is required")

    allowed_keys = ['host', 'port', 'ca_cert', 'cert_key', 'cert_cert',
                    'timeout', 'user', 'password']
    # TODO(evrardjp): Move this back to a dict comprehension when python 2.7 is
    # the minimum supported version
    # client_params = {key: value for key, value in module.params.items() if key in allowed_keys}
    client_params = dict()
    for key, value in module.params.items():
        if key in allowed_keys:
            client_params[key] = value
    try:
        etcd = etcd3.client(**client_params)
    except Exception as exp:
        module.fail_json(msg='Cannot connect to etcd cluster: %s' % (to_native(exp)),
                         exception=traceback.format_exc())
    if module.params['key'] != "":
        try:
            cluster_value = etcd.get(module.params['key'])
        except Exception as exp:
            module.fail_json(msg='Cannot reach data: %s' % (to_native(exp)),
                             exception=traceback.format_exc())

    # Make the cluster_value[0] a string for string comparisons
    result['old_value'] = to_native(cluster_value[0])

    if module.params['state'] == 'absent':
        if cluster_value[0] is not None:
            if module.check_mode:
                result['changed'] = True
            else:
                try:
                    etcd.delete(module.params['key'])
                except Exception as exp:
                    module.fail_json(msg='Cannot delete %s: %s' % (module.params['key'], to_native(exp)),
                                     exception=traceback.format_exc())
                else:
                    result['changed'] = True
    elif module.params['state'] == 'present':
        if result['old_value'] != module.params['value']:
            if module.check_mode:
                result['changed'] = True
            else:
                try:
                    etcd.put(module.params['key'], module.params['value'])
                except Exception as exp:
                    module.fail_json(msg='Cannot add or edit key %s: %s' % (module.params['key'], to_native(exp)),
                                     exception=traceback.format_exc())
                else:
                    result['changed'] = True
    elif module.params['state'] == 'absent_prefix':
        if etcd.get_prefix(module.params['key']):
            if module.check_mode:
                result['changed'] = True
            else:
                try:
                    etcd.delete_prefix(module.params['key'])
                except Exception as exp:
                    module.fail_json(msg='Cannot delete prefix %s: %s' % (module.params['key'], to_native(exp)),
                                     exception=traceback.format_exc())
                else:
                    result['changed'] = True
    else:
        module.fail_json(msg="State not recognized")

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
