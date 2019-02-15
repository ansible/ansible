#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community',
}

DOCUMENTATION = """
---
module: linode_v4
short_description: Manage instances on the Linode cloud.
description: Manage instances on the Linode cloud.
version_added: "2.8"
requirements:
  - python >= 2.7
  - linode_api4 >= 2.0.0
author:
  - Luke Murphy (@lwm)
notes:
  - No Linode resizing is currently implemented. This module will, in time,
    replace the current Linode module which uses deprecated API bindings on the
    Linode side.
options:
  region:
    description:
      - The region of the instance. This is a required parameter only when
        creating Linode instances. See
        U(https://developers.linode.com/api/v4#tag/Regions).
    required: false
    type: str
  image:
    description:
      - The image of the instance. This is a required parameter only when
        creating Linode instances. See
        U(https://developers.linode.com/api/v4#tag/Images).
    type: str
    required: false
  type:
    description:
      - The type of the instance. This is a required parameter only when
        creating Linode instances. See
        U(https://developers.linode.com/api/v4#tag/Linode-Types).
    type: str
    required: false
  label:
    description:
      - The instance label. This label is used as the main determiner for
        idempotence for the module and is therefore mandatory.
    type: str
    required: true
  group:
    description:
       - The group that the instance should be marked under. Please note, that
         group labelling is deprecated but still supported. The encouraged
         method for marking instances is to use tags.
    type: str
    required: false
  tags:
    description:
      - The tags that the instance should be marked under. See
        U(https://developers.linode.com/api/v4#tag/Tags).
    required: false
    type: list
  root_pass:
    description:
      - The password for the root user. If not specified, one will be
        generated. This generated password will be available in the task
        success JSON.
    required: false
    type: str
  authorized_keys:
    description:
      - A list of SSH public key parts to deploy for the root user.
    required: false
    type: list
  state:
    description:
      - The desired instance state.
    type: str
    choices:
        - present
        - absent
    required: true
  access_token:
    description:
      - The Linode API v4 access token. It may also be specified by exposing
        the C(LINODE_ACCESS_TOKEN) environment variable. See
        U(https://developers.linode.com/api/v4#section/Access-and-Authentication).
    required: true
"""

EXAMPLES = """
- name: Create a new Linode.
  linode_v4:
    label: new-linode
    type: g6-nanode-1
    region: eu-west
    image: linode/debian9
    root_pass: passw0rd
    authorized_keys:
      - "ssh-rsa ..."
    state: present

- name: Delete that new Linode.
  linode_v4:
    label: new-linode
    state: absent
"""

RETURN = """
instance:
  description: The instance description in JSON serialized form.
  returned: Always.
  type: dict
  sample: {
    "root_pass": "foobar",  # if auto-generated
    "alerts": {
      "cpu": 90,
      "io": 10000,
      "network_in": 10,
      "network_out": 10,
      "transfer_quota": 80
    },
    "backups": {
      "enabled": false,
      "schedule": {
        "day": null,
        "window": null
      }
    },
    "created": "2018-09-26T08:12:33",
    "group": "Foobar Group",
    "hypervisor": "kvm",
    "id": 10480444,
    "image": "linode/centos7",
    "ipv4": [
      "130.132.285.233"
    ],
    "ipv6": "2a82:7e00::h03c:46ff:fe04:5cd2/64",
    "label": "lin-foo",
    "region": "eu-west",
    "specs": {
      "disk": 25600,
      "memory": 1024,
      "transfer": 1000,
      "vcpus": 1
    },
    "status": "running",
    "tags": [],
    "type": "g6-nanode-1",
    "updated": "2018-09-26T10:10:14",
    "watchdog_enabled": true
  }
"""

import traceback

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib
from ansible.module_utils.linode import get_user_agent

LINODE_IMP_ERR = None
try:
    from linode_api4 import Instance, LinodeClient
    HAS_LINODE_DEPENDENCY = True
except ImportError:
    LINODE_IMP_ERR = traceback.format_exc()
    HAS_LINODE_DEPENDENCY = False


def create_linode(module, client, **kwargs):
    """Creates a Linode instance and handles return format."""
    if kwargs['root_pass'] is None:
        kwargs.pop('root_pass')

    try:
        response = client.linode.instance_create(**kwargs)
    except Exception as exception:
        module.fail_json(msg='Unable to query the Linode API. Saw: %s' % exception)

    try:
        if isinstance(response, tuple):
            instance, root_pass = response
            instance_json = instance._raw_json
            instance_json.update({'root_pass': root_pass})
            return instance_json
        else:
            return response._raw_json
    except TypeError:
        module.fail_json(msg='Unable to parse Linode instance creation'
                             ' response. Please raise a bug against this'
                             ' module on https://github.com/ansible/ansible/issues'
                         )


def maybe_instance_from_label(module, client):
    """Try to retrieve an instance based on a label."""
    try:
        label = module.params['label']
        result = client.linode.instances(Instance.label == label)
        return result[0]
    except IndexError:
        return None
    except Exception as exception:
        module.fail_json(msg='Unable to query the Linode API. Saw: %s' % exception)


def initialise_module():
    """Initialise the module parameter specification."""
    return AnsibleModule(
        argument_spec=dict(
            label=dict(type='str', required=True),
            state=dict(
                type='str',
                required=True,
                choices=['present', 'absent']
            ),
            access_token=dict(
                type='str',
                required=True,
                no_log=True,
                fallback=(env_fallback, ['LINODE_ACCESS_TOKEN']),
            ),
            authorized_keys=dict(type='list', required=False),
            group=dict(type='str', required=False),
            image=dict(type='str', required=False),
            region=dict(type='str', required=False),
            root_pass=dict(type='str', required=False, no_log=True),
            tags=dict(type='list', required=False),
            type=dict(type='str', required=False),
        ),
        supports_check_mode=False,
        required_one_of=(
            ['state', 'label'],
        ),
        required_together=(
            ['region', 'image', 'type'],
        )
    )


def build_client(module):
    """Build a LinodeClient."""
    return LinodeClient(
        module.params['access_token'],
        user_agent=get_user_agent('linode_v4_module')
    )


def main():
    """Module entrypoint."""
    module = initialise_module()

    if not HAS_LINODE_DEPENDENCY:
        module.fail_json(msg=missing_required_lib('linode-api4'), exception=LINODE_IMP_ERR)

    client = build_client(module)
    instance = maybe_instance_from_label(module, client)

    if module.params['state'] == 'present' and instance is not None:
        module.exit_json(changed=False, instance=instance._raw_json)

    elif module.params['state'] == 'present' and instance is None:
        instance_json = create_linode(
            module, client,
            authorized_keys=module.params['authorized_keys'],
            group=module.params['group'],
            image=module.params['image'],
            label=module.params['label'],
            region=module.params['region'],
            root_pass=module.params['root_pass'],
            tags=module.params['tags'],
            ltype=module.params['type'],
        )
        module.exit_json(changed=True, instance=instance_json)

    elif module.params['state'] == 'absent' and instance is not None:
        instance.delete()
        module.exit_json(changed=True, instance=instance._raw_json)

    elif module.params['state'] == 'absent' and instance is None:
        module.exit_json(changed=False, instance={})


if __name__ == "__main__":
    main()
