#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Mikhail Yohman (@FragmentedPacket) <mikhail.yohman@gmail.com>
# Copyright: (c) 2018, David Gomez (@amb1s1) <david.gomez@networktocode.com>
# Copyright: (c) 2019, Alvaro Arriola (@axarriola) <alvaroxarriola@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: netbox_vm
short_description: Create, update or delete virtual machines within Netbox
description:
  - Creates, updates or removes virtual machines from Netbox
notes:
  - Tags should be defined as a YAML list
  - This should be ran with connection C(local) and hosts C(localhost)
author:
  - Mikhail Yohman (@FragmentedPacket)
  - David Gomez (@amb1s1)
  - Alvaro Arriola (@axarriola)
requirements:
  - pynetbox
version_added: '2.9'
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
      role:
        description:
          - Required if I(state=present) and the virtual machine does not exist yet
      tenant:
        description:
          - The tenant that the virtual machine will be assigned to
      platform:
        description:
          - The platform of the virtual machine
      primary_ip:
        description:
          - Primary IP of the VM
      primary_ip4:
        description:
          - Primary IPv4 of the VM
      primary_ip6:
        description:
          - Primary IPv6 of the VM
      vcpus:
        description:
          - Number of vcpus assigned to VM
      memory:
        description:
          - Memory assigned to VM in MB
      disk:
        description:
          - Disk size in GB
      status:
        description:
          - The status of the virtual machine
        choices:
          - Active
          - Offline
          - Staged
      cluster:
        description:
          - Cluster that the virtual machine will be assigned to
      comments:
        description:
          - Comments that may include additional information in regards to the virtual machine
      tags:
        description:
          - Any tags that the virtual machine may need to be associated with
      custom_fields:
        description:
          - must exist in Netbox
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
    - name: Create VM within Netbox with only required information
      netbox_vm:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Test VM
          cluster: cluster1
          site: Main
        state: present

    - name: Delete VM within netbox
      netbox_vm:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Test VM
        state: absent

    - name: Update the vcpus and memory of an existing VM
      netbox_vm:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Test VM
          memory: 32000
          vcpus: 8
        state: present
'''

RETURN = r'''
virtual_machine:
  description: Serialized object as created or already existent within Netbox
  returned: success (when I(state=present))
  type: dict
msg:
  description: Message indicating failure or info about what has been achieved
  returned: always
  type: str
'''

import json
import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.net_tools.netbox.netbox_utils import (
    find_ids,
    normalize_data,
    create_netbox_object,
    delete_netbox_object,
    update_netbox_object,
    VM_STATUS,
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

    # Fail if VM name or cluster is not given
    if not module.params["data"].get("name") or not module.params["data"].get("cluster"):
        module.fail_json(msg="missing VM name/cluster")

    # Assign variables to be used with module
    app = 'virtualization'
    endpoint = 'virtual_machines'
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
            result = ensure_vm_present(nb, nb_endpoint, norm_data)
        else:
            result = ensure_vm_absent(nb_endpoint, norm_data)
        return module.exit_json(**result)
    except pynetbox.RequestError as e:
        return module.fail_json(msg=json.loads(e.error))
    except ValueError as e:
        return module.fail_json(msg=str(e))


def _find_ids(nb, data):
    if data.get("status"):
        data["status"] = VM_STATUS.get(data["status"].lower())
    return find_ids(nb, data)


def ensure_vm_present(nb, nb_endpoint, normalized_data):
    '''
    :returns dict(virtual_machine, msg, changed, diff): dictionary resulting of the request,
        where `virtual_machine` is the serialized VM fetched or newly created in
        Netbox
    '''
    data = _find_ids(nb, normalized_data)
    nb_vm = nb_endpoint.get(name=data["name"])
    result = {}
    if not nb_vm:
        vm, diff = create_netbox_object(nb_endpoint, data, module.check_mode)
        msg = "VM %s created" % (data["name"])
        changed = True
        result["diff"] = diff
    else:
        vm, diff = update_netbox_object(nb_vm, data, module.check_mode)
        if vm is False:
            module.fail_json(
                msg="Request failed, couldn't update VM: %s" % data["name"]
            )
        if diff:
            msg = "VM %s updated" % (data["name"])
            changed = True
            result["diff"] = diff
        else:
            msg = "VM %s already exists" % (data["name"])
            changed = False
    result.update({"virtual_machine": vm, "changed": changed, "msg": msg})
    return result


def ensure_vm_absent(nb_endpoint, data):
    '''
    :returns dict(msg, changed, diff)
    '''
    nb_vm = nb_endpoint.get(name=data["name"])
    result = {}
    if nb_vm:
        dummy, diff = delete_netbox_object(nb_vm, module.check_mode)
        msg = 'VM %s deleted' % (data["name"])
        changed = True
        result["diff"] = diff
    else:
        msg = 'VM %s already absent' % (data["name"])
        changed = False

    result.update({"changed": changed, "msg": msg})
    return result


if __name__ == "__main__":
    main()
