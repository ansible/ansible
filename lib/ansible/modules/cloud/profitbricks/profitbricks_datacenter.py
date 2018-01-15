#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: profitbricks_datacenter
short_description: Create or destroy a ProfitBricks Virtual Datacenter.
description:
     - This is a simple module that supports creating or removing vDCs. A vDC is required before you can create servers.
       This module has a dependency on profitbricks >= 1.0.0
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
    choices: [ "us/las", "us/ewr", "de/fra", "de/fkb" ]
  api_url:
    description:
      - The ProfitBricks API base URL.
    required: false
    default: The value specified by API_HOST variable in ProfitBricks SDK for Python dependency.
    version_added: "2.5"
  username:
    description:
      - The ProfitBricks username. Overrides the PROFITBRICKS_USERNAME environment variable.
    required: false
    aliases:
      - subscription_user
  password:
    description:
      - The ProfitBricks password. Overrides the PROFITBRICKS_PASSWORD environment variable.
    required: false
    aliases:
      - subscription_password
  wait:
    description:
      - wait for the datacenter to be created before returning
    required: false
    default: "yes"
    type: bool
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 600
  state:
    description:
      - Indicate desired state of the resource
    required: false
    default: 'present'
    choices: ["present", "absent", "update"]

requirements:
    - "python >= 2.6"
    - "profitbricks >= 4.0.0"
author:
    - "Matt Baldwin (baldwin@stackpointcloud.com)"
    - "Ethan Devenport (@edevenport)"
'''

EXAMPLES = '''

# Create a Datacenter
- profitbricks_datacenter:
    name: Example DC
    location: us/las
    wait_timeout: 500

# Update a datacenter description
- profitbricks_datacenter:
    name: Example DC
    description: test data center
    state: update

# Destroy a Datacenter. This will remove all servers, volumes, and other objects in the datacenter.
- profitbricks_datacenter:
    name: Example DC
    wait_timeout: 500
    state: absent

'''

HAS_PB_SDK = True

try:
    from profitbricks import API_HOST
    from profitbricks import __version__ as sdk_version
    from profitbricks.client import ProfitBricksService, Datacenter
except ImportError:
    HAS_PB_SDK = False

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils._text import to_native
from ansible.module_utils.profitbricks import (
    LOCATIONS,
    uuid_match,
    wait_for_completion
)


def _remove_datacenter(module, profitbricks, datacenter):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        profitbricks.delete_datacenter(datacenter)
    except Exception as e:
        module.fail_json(msg="failed to remove the datacenter: %s" % to_native(e))


def _update_datacenter(module, profitbricks, datacenter, description):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        profitbricks.update_datacenter(datacenter, description=description)
        return True
    except Exception as e:
        module.fail_json(msg="failed to update the datacenter: %s" % to_native(e))

    return False


def create_datacenter(module, profitbricks):
    """
    Creates a Datacenter

    This will create a new Datacenter in the specified location.

    module : AnsibleModule object
    profitbricks: authenticated profitbricks object.

    Returns:
        The datacenter ID if a new datacenter was created.
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
            wait_for_completion(profitbricks, datacenter_response,
                                wait_timeout, "_create_datacenter")

        results = {
            'datacenter_id': datacenter_response['id']
        }

        return results

    except Exception as e:
        module.fail_json(msg="failed to create the new datacenter: %s" % to_native(e))


def update_datacenter(module, profitbricks):
    """
    Updates a Datacenter.

    This will update a datacenter.

    module : AnsibleModule object
    profitbricks: authenticated profitbricks object.

    Returns:
        True if a new datacenter was updated, false otherwise
    """
    name = module.params.get('name')
    description = module.params.get('description')

    if description is None:
        return False

    changed = False

    if(uuid_match.match(name)):
        changed = _update_datacenter(module, profitbricks, name, description)
    else:
        datacenters = profitbricks.list_datacenters()

        for d in datacenters['items']:
            vdc = profitbricks.get_datacenter(d['id'])

            if name == vdc['properties']['name']:
                name = d['id']
                changed = _update_datacenter(module, profitbricks, name, description)

    return changed


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
            name=dict(type='str'),
            description=dict(type='str'),
            location=dict(type='str', choices=LOCATIONS, default='us/las'),
            api_url=dict(type='str', default=API_HOST),
            username=dict(
                required=True,
                aliases=['subscription_user'],
                fallback=(env_fallback, ['PROFITBRICKS_USERNAME'])
            ),
            password=dict(
                required=True,
                aliases=['subscription_password'],
                fallback=(env_fallback, ['PROFITBRICKS_PASSWORD']),
                no_log=True
            ),
            wait=dict(type='bool', default=True),
            wait_timeout=dict(type='int', default=600),
            state=dict(type='str', default='present'),
        ),
        supports_check_mode=True
    )
    if not HAS_PB_SDK:
        module.fail_json(msg='profitbricks required for this module')

    username = module.params.get('username')
    password = module.params.get('password')
    api_url = module.params.get('api_url')

    profitbricks = ProfitBricksService(
        username=username,
        password=password,
        host_base=api_url
    )

    user_agent = 'profitbricks-sdk-python/%s Ansible/%s' % (sdk_version, module.ansible_version)
    profitbricks.headers = {'User-Agent': user_agent}

    state = module.params.get('state')

    if state == 'absent':
        if not module.params.get('name'):
            module.fail_json(msg='name parameter is required deleting a virtual datacenter.')

        try:
            (changed) = remove_datacenter(module, profitbricks)
            module.exit_json(
                changed=changed)
        except Exception as e:
            module.fail_json(msg='failed to set datacenter state: %s' % to_native(e))

    elif state == 'present':
        if not module.params.get('name'):
            module.fail_json(msg='name parameter is required for a new datacenter')
        if not module.params.get('location'):
            module.fail_json(msg='location parameter is required for a new datacenter')

        if module.check_mode:
            module.exit_json(changed=True)

        try:
            (datacenter_dict_array) = create_datacenter(module, profitbricks)
            module.exit_json(**datacenter_dict_array)
        except Exception as e:
            module.fail_json(msg='failed to set datacenter state: %s' % to_native(e))

    elif state == 'update':
        try:
            (changed) = update_datacenter(module, profitbricks)
            module.exit_json(changed=changed)
        except Exception as e:
            module.fail_json(msg='failed to update datacenter: %s' % to_native(e))


if __name__ == '__main__':
    main()
