#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/license  s/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: linode_v4

short_description: create, destroy, and update linode's simply

version_added: "2.7"

options:
    type:
        description:
            - the resource size for the linode instance. More info can be
              found here, as the id key: https://api.linode.com/v4/linode/types
        required: true
    region:
        description:
            - region to provision the instance, only needed when creating or
              updating the instance. Options be found here:
              https://api.linode.com/v4/regions
        required: true
    image:
        description:
            - image to boot the instance from. You should be able to boot
              images that are private to your account, you would just need to
              find the id key from the list of image objects. Publically
              available images can be found here:
              https://api.linode.com/v4/images
        required: true
    state:
        description:
            - can be either absent or present, absent deletes the image and has
              a strict requirement on a label. present will either assure that
              a previously created image exists or create a new one. Do note
              that labels are unique.
        required: true
    label:
        description:
            - can be either absent or present, absent deletes the image and has
              a strict requirement on a label. present will either assure that
              a previously created image exists or create a new one. Do note
              that labels are unique.
        required: false
    token:
        description:
            - string to authenticate against the linode api, not required as
              the module will check for a LINODE_TOKEN environment variable on
              the control machine.
        required: false

extends_documentation_fragment:
    - linode

author:
    - Your Name (@rwaweber)
"""

EXAMPLES = """
- name: create a nameless linode instance
  linode_v4:
    type: g6-nanode-1
    region: us-east
    image: "linode/centos7"
    state: present

- name: attempt to create a linode instance
  linode_v4:
    type: g6-nanode-1
    region: us-east
    image: "linode/centos7"
    label: ansible-managed-testbox
    state: present
  register: create_response

- debug:
    msg: "{{ create_response }}"

- name: delete the instance we just created
  linode_v4:
    type: g6-nanode-1
    region: us-east
    image: "linode/centos7"
    state: absent
    label: ansible-managed-testbox
  register: delete_response

- debug:
    msg: "{{ delete_response }}"
"""

RETURN = """
data:
    description: the response from the linode api on creation and removal. More information
    can be found here: https://developers.linode.com/api/v4#operation/createLinodeInstance
"""

import json
import os
import random
import string
import time

from ansible.module_utils.basic import AnsibleModule
import requests


def delete_linode(module, instance_id, label, token):
    """
    delete a linode instance
    """
    delete_response = requests.delete(
        "https://api.linode.com/v4/linode/instances/{0}".format(instance_id),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {0}".format(token),
        },
        data=json.dumps({"linodeId": instance_id}),
    )
    if not delete_response:
        module.fail_json(
            msg="issue deleting linode: {0} with id: {1}".format(label, instance_id)
        )
    return delete_response.json()


def list_linode(module, token):
    """
    return linode instance data
    """
    list_response = requests.get(
        "https://api.linode.com/v4/linode/instances",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {0}".format(token),
        },
        data=json.dumps({"page_size": 100}),
    )
    if not list_response:
        module.fail_json(msg="issue creating linode: {0}".format(list_response.json()))
    return list_response.json()


def get_instance_by_label(module, label, token):
    """
    retrieve instance information by label
    """
    list_response = list_linode(module, token)
    matched_instances = [
        entry for entry in list_response["data"] if label in entry["label"]
    ]
    if matched_instances:
        return matched_instances[0]
    return False


def create_linode(module, root_pass, token):
    """
    creates an instance and returns the ip addresses
    """
    create_response = requests.post(
        "https://api.linode.com/v4/linode/instances",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {0}".format(token),
        },
        data=json.dumps(
            {
                "label": module.params["label"],
                "type": module.params["type"],
                "region": module.params["region"],
                "image": module.params["image"],
                "root_pass": root_pass,
                "authorized_keys": module.params["authorized_keys"],
            }
        ),
    )
    if not create_response:
        module.fail_json(
            msg="issue creating linode: {0}".format(create_response.json())
        )
    return create_response.json()


def rebuild_linode(module, root_pass, instance_id, token):
    """
    rebuild an instance to the specified parameters, should boot on its own
    """
    rebuild_response = requests.post(
        "https://api.linode.com/v4/linode/instances/{0}/rebuild".format(instance_id),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {0}".format(token),
        },
        data=json.dumps(
            {
                "image": module.params["image"],
                "root_pass": root_pass,
                "authorized_keys": module.params["authorized_keys"],
            }
        ),
    )
    if not rebuild_response:
        module.fail_json(
            msg="issue rebuilding linode: {0}".format(rebuild_response.json())
        )

    return rebuild_response.json()


def resize_linode(module, instance_id, token, ignore_error=False):
    """
    resizes an instance to the specified format and then boots it
    """
    resize_response = requests.post(
        "https://api.linode.com/v4/linode/instances/{0}/resize".format(instance_id),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {0}".format(token),
        },
        data=json.dumps({"type": module.params["type"]}),
    )
    # exit early if we are supposed to ignore errors
    if not resize_response:
        module.fail_json(
            msg="issue resizing linode: {0}".format(resize_response.json())
        )

    boot_response = requests.post(
        "https://api.linode.com/v4/linode/instances/{0}/boot".format(instance_id),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {0}".format(token),
        },
    )
    if not boot_response:
        module.fail_json(
            msg="issue booting linode after resize: {0}".format(boot_response.json())
        )

    return boot_response.json()


def run_module():
    """
    consumes module parameters and performs some operations
    """
    module_args = dict(
        type=dict(type="str", required=True),
        region=dict(type="str", required=True),
        image=dict(type="str", required=True),
        state=dict(type="str", required=True),
        label=dict(type="str", required=False),
        authorized_keys=dict(type="list", required=False),
        token=dict(type="str", required=False),
    )

    result = dict(changed=False, data="")

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)

    # check for exported authorization token
    try:
        token = os.environ["LINODE_TOKEN"]
    except KeyError:
        token = module.params["token"]
    except KeyError:
        module.fail_json(
            msg="Need to pass in an access token either as LINODE_TOKEN environment variable or as 'token' as a module parameter"
        )

    # We want to check to see if a labeled linode exists on the account. If not, create one.
    # If no label is specified we should be able to skip this check and save some bandwidth.
    # Note that if we do that, it will get a randomly assigned name that would need to be
    # used later if we would like to manage it.
    if module.params["state"] == "present":
        if module.params["label"]:
            matched_instance = get_instance_by_label(
                module, module.params["label"], token
            )

            if not matched_instance:
                # create a new linode instance with passed parameters
                response_json = create_linode(
                    module,
                    # randomly generated password of 45 characters
                    "".join(
                        random.choice(string.ascii_uppercase + string.digits)
                        for _ in range(45)
                    ),
                    token,
                )
                result["changed"] = True
                result["data"] = response_json
                module.exit_json(**result)

            # if the instance whose label matched has a discrepancy between the image
            # selected it will be rebuilt.
            # https://developers.linode.com/api/v4#operation/rebuildLinodeInstance
            # unfortunately, we cannot rebuild into an instance size larger
            # than what was originally allocated -- if there is a difference
            # we will induce a resize operation after the rebuild to meet the
            # desired state in the module parameters. This should be transparent
            # to the user but on the linode side it will result in the rebuilt image
            # being rebooted turned down, resized, and then booted.

            if matched_instance["image"] != module.params["image"]:
                rebuild_json = rebuild_linode(
                    module,
                    "".join(
                        random.choice(string.ascii_uppercase + string.digits)
                        for _ in range(45)
                    ),
                    matched_instance["id"],
                    token,
                )

                # if the size of the newly rebuilt instance doesn't match, wait
                # some time before trying to resize it. The api will return busy
                # errors until the rebuild is complete.
                if matched_instance["type"] != module.params["type"]:
                    time.sleep(60)
                    resize_json = resize_linode(module, matched_instance["id"], token)
                    result["data"] = resize_json
                    result["changed"] = True
                    module.exit_json(**result)

                result["data"] = rebuild_json
                result["changed"] = True
                module.exit_json(**result)

            # if there is a discrepancy between only the resource type and the selected
            # resource type it will be resized:
            # https://developers.linode.com/api/v4#operation/resizeLinodeInstance
            if matched_instance["type"] != module.params["type"]:
                resize_json = resize_linode(module, matched_instance["id"], token)
                result["data"] = resize_json
                result["changed"] = True
                module.exit_json(**result)

            # Finally, if there are no discrepancies and the linode already
            # exists, we don't need to change anything
            elif matched_instance:
                result["data"] = matched_instance
                result["changed"] = False
                module.exit_json(**result)

    # instance destruction flow
    elif module.params["state"] == "absent":
        # label parameter is required to delete an instance
        if not module.params["label"]:
            module.exit_json(msg="label is required to delete an instance")
        # find the instance by the provided label
        # this will request the list of instances on a given account and filter
        # on the label
        matched_instance = get_instance_by_label(module, module.params["label"], token)
        if not matched_instance:
            result["data"] = matched_instance
            result["changed"] = False
            module.exit_json(**result)

        delete_linode(module, matched_instance["id"], matched_instance["label"], token)
        result["data"] = matched_instance
        result["changed"] = True
        module.exit_json(**result)
    return None


if __name__ == "__main__":
    run_module()
