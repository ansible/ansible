#!/usr/bin/python
# Copyright 2017 Google Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: gce_eip
version_added: "2.3"
short_description: Create or Destroy Global or Regional External IP addresses.
description:
    - Create (reserve) or Destroy (release) Regional or Global IP Addresses. See
      U(https://cloud.google.com/compute/docs/configure-instance-ip-addresses#reserve_new_static) for more on reserving static addresses.
requirements:
  - "python >= 2.6"
  - "apache-libcloud >= 0.19.0"
notes:
  - Global addresses can only be used with Global Forwarding Rules.
author:
  - "Tom Melendez (@supertom) <tom@supertom.com>"
options:
  name:
    description:
       - Name of Address.
    required: true
  region:
    description:
       - Region to create the address in. Set to 'global' to create a global address.
    required: true
  state:
    description: The state the address should be in. C(present) or C(absent) are the only valid options.
    default: present
    required: false
    choices: [present, absent]
'''

EXAMPLES = '''
# Create a Global external IP address
gce_eip:
  service_account_email: "{{ service_account_email }}"
  credentials_file: "{{ credentials_file }}"
  project_id: "{{ project_id }}"
  name: my-global-ip
  region: global
  state: present

# Create a Regional external IP address
gce_eip:
  service_account_email: "{{ service_account_email }}"
  credentials_file: "{{ credentials_file }}"
  project_id: "{{ project_id }}"
  name: my-global-ip
  region: us-east1
  state: present
'''

RETURN = '''
address:
    description: IP address being operated on
    returned: always
    type: string
    sample: "35.186.222.233"
name:
    description: name of the address being operated on
    returned: always
    type: string
    sample: "my-address"
region:
    description: Which region an address belongs.
    returned: always
    type: string
    sample: "global"
'''

USER_AGENT_VERSION = 'v1'
USER_AGENT_PRODUCT = 'Ansible-gce_eip'

try:
    from ast import literal_eval
    HAS_PYTHON26 = True
except ImportError:
    HAS_PYTHON26 = False

try:
    import libcloud
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    from libcloud.common.google import GoogleBaseError, QuotaExceededError, \
        ResourceExistsError, ResourceInUseError, ResourceNotFoundError
    from libcloud.compute.drivers.gce import GCEAddress
    _ = Provider.GCE
    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gcp import gcp_connect


def get_address(gce, name, region):
    """
    Get an Address from GCE.

    :param gce: An initialized GCE driver object.
    :type gce:  :class: `GCENodeDriver`

    :param name: Name of the Address.
    :type name:  ``str``

    :return: A GCEAddress object or None.
    :rtype: :class: `GCEAddress` or None
    """
    try:
        return gce.ex_get_address(name=name, region=region)

    except ResourceNotFoundError:
        return None

def create_address(gce, params):
    """
    Create a new Address.

    :param gce: An initialized GCE driver object.
    :type gce:  :class: `GCENodeDriver`

    :param params: Dictionary of parameters needed by the module.
    :type params:  ``dict``

    :return: Tuple with changed status and address.
    :rtype: tuple in the format of (bool, str)
    """
    changed = False
    return_data = []

    address = gce.ex_create_address(
        name=params['name'], region=params['region'])

    if address:
        changed = True
        return_data = address.address

    return (changed, return_data)

def delete_address(address):
    """
    Delete an Address.

    :param gce: An initialized GCE driver object.
    :type gce:  :class: `GCENodeDriver`

    :param params: Dictionary of parameters needed by the module.
    :type params:  ``dict``

    :return: Tuple with changed status and address.
    :rtype: tuple in the format of (bool, str)
    """
    changed = False
    return_data = []
    if address.destroy():
        changed = True
        return_data = address.address
    return (changed, return_data)

def main():
    module = AnsibleModule(argument_spec=dict(
        name=dict(required=True),
        state=dict(choices=['absent', 'present'], default='present'),
        region=dict(required=True),
        service_account_email=dict(),
        service_account_permissions=dict(type='list'),
        pem_file=dict(type='path'),
        credentials_file=dict(type='path'),
        project_id=dict(), ), )

    if not HAS_PYTHON26:
        module.fail_json(
            msg="GCE module requires python's 'ast' module, python v2.6+")
    if not HAS_LIBCLOUD:
        module.fail_json(
            msg='libcloud with GCE support (+0.19) required for this module.')

    gce = gcp_connect(module, Provider.GCE, get_driver,
                      USER_AGENT_PRODUCT, USER_AGENT_VERSION)

    params = {}
    params['state'] = module.params.get('state')
    params['name'] = module.params.get('name')
    params['region'] = module.params.get('region')

    changed = False
    json_output = {'state': params['state']}
    address = get_address(gce, params['name'], region=params['region'])

    if params['state'] == 'absent':
        if not address:
            # Doesn't exist in GCE, and state==absent.
            changed = False
            module.fail_json(
                msg="Cannot delete unknown address: %s" %
                (params['name']))
        else:
            # Delete
            (changed, json_output['address']) = delete_address(address)
    else:
        if not address:
            # Create
            (changed, json_output['address']) = create_address(gce,
                                                               params)
        else:
            changed = False
            json_output['address'] = address.address

    json_output['changed'] = changed
    json_output.update(params)
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
