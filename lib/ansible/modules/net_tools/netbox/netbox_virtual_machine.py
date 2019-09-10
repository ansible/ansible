#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Mikhail Yohman (@FragmentedPacket) <mikhail.yohman@gmail.com>
# Copyright: (c) 2018, David Gomez (@amb1s1) <david.gomez@networktocode.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: netbox_virtual_machine
short_description: Create, update or delete virtual_machines within Netbox
description:
  - Creates, updates or removes virtual_machines from Netbox
notes:
  - Tags should be defined as a YAML list
  - This should be ran with connection C(local) and hosts C(localhost)
author:
  - Mikhail Yohman (@FragmentedPacket)
  - David Gomez (@amb1s1)
  - Gaelle MANGIN (@gmangin)
requirements:
  - pynetbox
version_added: '2.8'
options:
  netbox_url:
    description:
      - URL of the Netbox instance resolvable by Ansible control host
    required: true
  netbox_token:
    description:
      - The token created within Netbox to authorize API access
    required: true
  data:
    description:
      - Defines the virtual machine configuration
    suboptions:
      name:
        description:
          - The name of the virtual machine
        required: true
      cluster:
        description:
          - The name of the cluster attach to the virtual machine
        required: true
      role:
        description:
          - The role of the virtual machine
      vcpus:
        description:
          - Number of vcpus of the virtual machine
      tenant:
        description:
          - The tenant that the virtual machine will be assigned to
      platform:
        description:
          - The platform of the virtual machine
      memory:
        description:
          - Memory of the virtual machine (MB)
      disk:
        description:
          - Disk of the virtual machine (GB)
      site:
        description:
          - Required if I(state=present) and the virtual machine does not exist yet
      rack:
        description:
          - The name of the rack to assign the virtual machine to
      status:
        description:
          - The status of the virtual machine
        choices:
          - Active
          - Offline
          - Staged
      tags:
        description:
          - Any tags that the virtual machine may need to be associated with
    required: true
  state:
    description:
      - Use C(present) or C(absent) for adding or removing.
    choices: [ absent, present ]
    default: present
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used on personally controlled sites using self-signed certificates.
    default: 'yes'
    type: bool
'''

EXAMPLES = r'''
- name: "Test Netbox modules"
  connection: local
  hosts: localhost
  gather_facts: False

  tasks:
    - name: Create virtual machine within Netbox with only required information
      netbox_virtual_machine:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Test Virtual Machine
          cluster: test cluster
        state: present

    - name: Delete virtual machine within netbox
      netbox_virtual_machine:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Test Virtual Machine
        state: absent

    - name: Create virtual machine with tags
      netbox_virtual_machine:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Another Test Virtual Machine
          cluster: test cluster
          tags:
            - Schnozzberry
        state: present

    - name: Update vcpus, memory and disk of an existing virtual machine
      netbox_virtual_machine:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Test Virtual Machine
          cluster: test cluster
          vcpus: 8
          memory: 8
          disk: 8
        state: present
'''

RETURN = r'''
virtual machine:
  description: Serialized object as created or already existent within Netbox
  returned: success (when I(state=present))
  type: dict
msg:
  description: Message indicating failure or info about what has been achieved
  returned: always
  type: str
'''

# import module snippets
import json
import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.net_tools.netbox.netbox_utils import (
    find_ids,
    normalize_data,
    create_netbox_object,
    delete_netbox_object,
    update_netbox_object,
    VIRTUAL_MACHINE_STATUS,
    FACE_ID
)

PYNETBOX_IMP_ERR = None
try:
    import pynetbox
    HAS_PYNETBOX = True
except ImportError:
    PYNETBOX_IMP_ERR = traceback.format_exc()
    HAS_PYNETBOX = False

def main():
    '''
    Main entry point for module execution
    '''
    argument_spec = dict(
        netbox_url=dict(type="str", required=True),
        netbox_token=dict(type="str", required=True, no_log=True),
        data=dict(type="dict", required=True),
        state=dict(required=False, default='present', choices=['present', 'absent']),
        validate_certs=dict(type="bool", default=True)
    )

    global module
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    # Fail module if pynetbox is not installed
    if not HAS_PYNETBOX:
        module.fail_json(msg=missing_required_lib('pynetbox'), exception=PYNETBOX_IMP_ERR)

    # Fail if virtual_machine name is not given
    if not module.params["data"].get("name"):
        module.fail_json(msg="missing virtual_machine name")

    # Assign variables to be used with module
    app = 'virtualization'
    endpoint = 'virtual-machines'
    url = module.params["netbox_url"]
    token = module.params["netbox_token"]
    data = module.params["data"]
    state = module.params["state"]
    validate_certs = module.params["validate_certs"]

    # Attempt to create Netbox API object
    try:
       nb = pynetbox.api(url, token=token, ssl_verify=validate_certs)
    except Exception:
        module.fail_json(msg="Failed to establish connection to Netbox API")
    try:
        nb_app = getattr(nb, app)
    except AttributeError:
        module.fail_json(msg="Incorrect application specified: %s" % (app))

    nb_endpoint = getattr(nb_app, endpoint)
    norm_data = normalize_data(data)
    try:
        if 'present' in state:
            result = ensure_virtual_machine_present(nb, nb_endpoint, norm_data)
        else:
            result = ensure_virtual_machine_absent(nb_endpoint, norm_data)
        return module.exit_json(**result)
    except pynetbox.RequestError as e:
        return module.fail_json(msg=json.loads(e.error))
    except ValueError as e:
        return module.fail_json(msg=str(e))

def _find_ids(nb, data):
    if data.get("status"):
        data["status"] = VIRTUAL_MACHINE_STATUS.get(data["status"].lower())
    if data.get("face"):
        data["face"] = FACE_ID.get(data["face"].lower())
    return find_ids(nb, data)

def ensure_virtual_machine_present(nb, nb_endpoint, normalized_data):
    '''
    :returns dict(virtual_machine, msg, changed, diff): dictionary resulting of the request,
        where `virtual_machine` is the serialized virtual_machine fetched or newly created in
        Netbox
    '''
    data = _find_ids(nb, normalized_data)
    nb_virtual_machine = nb_endpoint.get(name=data["name"])
    result = {}
    if not nb_virtual_machine:
        virtual_machine, diff = create_netbox_object(nb_endpoint, data, module.check_mode)
        msg = "Virtual_Machine %s created" % (data["name"])
        changed = True
        result["diff"] = diff
    else:
        virtual_machine, diff = update_netbox_object(nb_virtual_machine, data, module.check_mode)
        if virtual_machine is False:
            module.fail_json(
                msg="Request failed, couldn't update virtual_machine: %s" % data["name"]
            )
        if diff:
            msg = "Virtual_Machine %s updated" % (data["name"])
            changed = True
            result["diff"] = diff
        else:
            msg = "Virtual_Machine %s already exists" % (data["name"])
            changed = False
    result.update({"virtual_machine": virtual_machine, "changed": changed, "msg": msg})
    return result

def ensure_virtual_machine_absent(nb_endpoint, data):
    '''
    :returns dict(msg, changed, diff)
    '''
    nb_virtual_machine = nb_endpoint.get(name=data["name"])
    result = {}
    if nb_virtual_machine:
        dummy, diff = delete_netbox_object(nb_virtual_machine, module.check_mode)
        msg = 'Virtual_Machine %s deleted' % (data["name"])
        changed = True
        result["diff"] = diff
    else:
        msg = 'Virtual_Machine %s already absent' % (data["name"])
        changed = False

    result.update({"changed": changed, "msg": msg})
    return result

if __name__ == '__main__':
    main()
