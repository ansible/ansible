#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: profitbricks_datacenter
short_description: Create or destroy a ProfitBricks Virtual Datacenter.
description:
     - This is a simple module that supports creating or removing vDCs. A vDC is required before you can create servers. This module has a dependency
       on profitbricks >= 1.0.0
version_added: "2.0"
options:
  name:
    description:
      - The name of the virtual datacenter.
    required: true
  description:
    description:
      - The description of the virtual datacenter.
    required: false
  location:
    description:
      - The datacenter location.
    required: false
    default: us/las
    choices: [ "us/las", "de/fra", "de/fkb" ]
  subscription_user:
    description:
      - The ProfitBricks username. Overrides the PB_SUBSCRIPTION_ID environment variable.
    required: false
  subscription_password:
    description:
      - THe ProfitBricks password. Overrides the PB_PASSWORD environment variable.
    required: false
  wait:
    description:
      - wait for the datacenter to be created before returning
    required: false
    default: "yes"
    choices: [ "yes", "no" ]
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 600
  state:
    description:
      - create or terminate datacenters
    required: false
    default: 'present'
    choices: [ "present", "absent" ]

requirements: [ "profitbricks" ]
author: Matt Baldwin (baldwin@stackpointcloud.com)
'''

EXAMPLES = '''

# Create a Datacenter
- profitbricks_datacenter:
    datacenter: Tardis One
    wait_timeout: 500

# Destroy a Datacenter. This will remove all servers, volumes, and other objects in the datacenter.
- profitbricks_datacenter:
    datacenter: Tardis One
    wait_timeout: 500
    state: absent

'''

import re
import time

HAS_PB_SDK = True
try:
    from profitbricks.client import ProfitBricksService, Datacenter
except ImportError:
    HAS_PB_SDK = False

from ansible.module_utils.basic import AnsibleModule


LOCATIONS = ['us/las',
             'de/fra',
             'de/fkb']

uuid_match = re.compile(
    '[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}', re.I)


def _wait_for_completion(profitbricks, promise, wait_timeout, msg):
    if not promise:
        return
    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time():
        time.sleep(5)
        operation_result = profitbricks.get_request(
            request_id=promise['requestId'],
            status=True)

        if operation_result['metadata']['status'] == "DONE":
            return
        elif operation_result['metadata']['status'] == "FAILED":
            raise Exception(
                'Request failed to complete ' + msg + ' "' + str(
                    promise['requestId']) + '" to complete.')

    raise Exception(
        'Timed out waiting for async operation ' + msg + ' "' + str(
            promise['requestId']
            ) + '" to complete.')

def _remove_datacenter(module, profitbricks, datacenter):
    try:
        profitbricks.delete_datacenter(datacenter)
    except Exception as e:
        module.fail_json(msg="failed to remove the datacenter: %s" % str(e))

def create_datacenter(module, profitbricks):
    """
    Creates a Datacenter

    This will create a new Datacenter in the specified location.

    module : AnsibleModule object
    profitbricks: authenticated profitbricks object.

    Returns:
        True if a new datacenter was created, false otherwise
    """
    name = module.params.get('name')
    location = module.params.get('location')
    description = module.params.get('description')
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))

    i = Datacenter(
        name=name,
        location=location,
        description=description
        )

    try:
        datacenter_response = profitbricks.create_datacenter(datacenter=i)

        if wait:
            _wait_for_completion(profitbricks, datacenter_response,
                                 wait_timeout, "_create_datacenter")

        results = {
            'datacenter_id': datacenter_response['id']
        }

        return results

    except Exception as e:
        module.fail_json(msg="failed to create the new datacenter: %s" % str(e))

def remove_datacenter(module, profitbricks):
    """
    Removes a Datacenter.

    This will remove a datacenter.

    module : AnsibleModule object
    profitbricks: authenticated profitbricks object.

    Returns:
        True if the datacenter was deleted, false otherwise
    """
    name = module.params.get('name')
    changed = False

    if(uuid_match.match(name)):
        _remove_datacenter(module, profitbricks, name)
        changed = True
    else:
        datacenters = profitbricks.list_datacenters()

        for d in datacenters['items']:
            vdc = profitbricks.get_datacenter(d['id'])

            if name == vdc['properties']['name']:
                name = d['id']
                _remove_datacenter(module, profitbricks, name)
                changed = True

    return changed

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(),
            description=dict(),
            location=dict(choices=LOCATIONS, default='us/las'),
            subscription_user=dict(),
            subscription_password=dict(no_log=True),
            wait=dict(type='bool', default=True),
            wait_timeout=dict(default=600),
            state=dict(default='present'),
        )
    )
    if not HAS_PB_SDK:
        module.fail_json(msg='profitbricks required for this module')

    if not module.params.get('subscription_user'):
        module.fail_json(msg='subscription_user parameter is required')
    if not module.params.get('subscription_password'):
        module.fail_json(msg='subscription_password parameter is required')

    subscription_user = module.params.get('subscription_user')
    subscription_password = module.params.get('subscription_password')

    profitbricks = ProfitBricksService(
        username=subscription_user,
        password=subscription_password)

    state = module.params.get('state')

    if state == 'absent':
        if not module.params.get('name'):
            module.fail_json(msg='name parameter is required deleting a virtual datacenter.')

        try:
            (changed) = remove_datacenter(module, profitbricks)
            module.exit_json(
                changed=changed)
        except Exception as e:
            module.fail_json(msg='failed to set datacenter state: %s' % str(e))

    elif state == 'present':
        if not module.params.get('name'):
            module.fail_json(msg='name parameter is required for a new datacenter')
        if not module.params.get('location'):
            module.fail_json(msg='location parameter is required for a new datacenter')

        try:
            (datacenter_dict_array) = create_datacenter(module, profitbricks)
            module.exit_json(**datacenter_dict_array)
        except Exception as e:
            module.fail_json(msg='failed to set datacenter state: %s' % str(e))


if __name__ == '__main__':
    main()
