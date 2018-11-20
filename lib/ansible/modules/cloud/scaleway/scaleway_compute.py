#!/usr/bin/python
#
# Scaleway Compute management module
#
# Copyright (C) 2018 Online SAS.
# https://www.scaleway.com
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: scaleway_compute
short_description: Scaleway compute management module
version_added: "2.6"
author: Remy Leone (@sieben)
description:
    - "This module manages compute instances on Scaleway."
extends_documentation_fragment: scaleway

options:

  public_ip:
    description:
    - Manage public IP on a Scaleway server
    - Could be Scaleway IP address UUID
    - C(dynamic) Means that IP is destroyed at the same time the host is destroyed
    - C(absent) Means no public IP at all
    version_added: '2.8'
    default: absent

  enable_ipv6:
    description:
      - Enable public IPv6 connectivity on the instance
    default: false
    type: bool

  image:
    description:
      - Image identifier used to start the instance with
    required: true

  name:
    description:
      - Name of the instance

  organization:
    description:
      - Organization identifier
    required: true

  state:
    description:
     - Indicate desired state of the instance.
    default: present
    choices:
      - present
      - absent
      - running
      - restarted
      - stopped

  tags:
    description:
    - List of tags to apply to the instance (5 max)
    required: false
    default: []

  region:
    description:
    - Scaleway compute zone
    required: true
    choices:
      - ams1
      - EMEA-NL-EVS
      - par1
      - EMEA-FR-PAR1

  commercial_type:
    description:
    - Commercial name of the compute node
    required: true
    choices:
      - ARM64-2GB
      - ARM64-4GB
      - ARM64-8GB
      - ARM64-16GB
      - ARM64-32GB
      - ARM64-64GB
      - ARM64-128GB
      - C1
      - C2S
      - C2M
      - C2L
      - START1-XS
      - START1-S
      - START1-M
      - START1-L
      - X64-15GB
      - X64-30GB
      - X64-60GB
      - X64-120GB

  wait:
    description:
    - Wait for the instance to reach its desired state before returning.
    type: bool
    default: 'no'

  wait_timeout:
    description:
    - Time to wait for the server to reach the expected state
    required: false
    default: 300

  wait_sleep_time:
    description:
    - Time to wait before every attempt to check the state of the server
    required: false
    default: 3

  security_group:
    description:
    - Security group unique identifier
    - If no value provided, the default security group or current security group will be used
    required: false
    version_added: "2.8"
'''

EXAMPLES = '''
- name: Create a server
  scaleway_compute:
    name: foobar
    state: present
    image: 89ee4018-f8c3-4dc4-a6b5-bca14f985ebe
    organization: 951df375-e094-4d26-97c1-ba548eeb9c42
    region: ams1
    commercial_type: START1-S
    tags:
      - test
      - www

- name: Create a server attached to a security group
  scaleway_compute:
    name: foobar
    state: present
    image: 89ee4018-f8c3-4dc4-a6b5-bca14f985ebe
    organization: 951df375-e094-4d26-97c1-ba548eeb9c42
    region: ams1
    commercial_type: START1-S
    security_group: 4a31b633-118e-4900-bd52-facf1085fc8d
    tags:
      - test
      - www

- name: Destroy it right after
  scaleway_compute:
    name: foobar
    state: absent
    image: 89ee4018-f8c3-4dc4-a6b5-bca14f985ebe
    organization: 951df375-e094-4d26-97c1-ba548eeb9c42
    region: ams1
    commercial_type: START1-S
'''

RETURN = '''
'''

import datetime
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import quote as urlquote
from ansible.module_utils.scaleway import SCALEWAY_LOCATION, scaleway_argument_spec, Scaleway

SCALEWAY_COMMERCIAL_TYPES = [

    # Virtual ARM64 compute instance
    'ARM64-2GB',
    'ARM64-4GB',
    'ARM64-8GB',
    'ARM64-16GB',
    'ARM64-32GB',
    'ARM64-64GB',
    'ARM64-128GB',

    # Baremetal
    'C1',  # ARM64 (4 cores) - 2GB
    'C2S',  # X86-64 (4 cores) - 8GB
    'C2M',  # X86-64 (8 cores) - 16GB
    'C2L',  # x86-64 (8 cores) - 32 GB

    # Virtual X86-64 compute instance
    'START1-XS',  # Starter X86-64 (1 core) - 1GB - 25 GB NVMe
    'START1-S',  # Starter X86-64 (2 cores) - 2GB - 50 GB NVMe
    'START1-M',  # Starter X86-64 (4 cores) - 4GB - 100 GB NVMe
    'START1-L',  # Starter X86-64 (8 cores) - 8GB - 200 GB NVMe
    'X64-15GB',
    'X64-30GB',
    'X64-60GB',
    'X64-120GB',
]

SCALEWAY_SERVER_STATES = (
    'stopped',
    'stopping',
    'starting',
    'running',
    'locked'
)

SCALEWAY_TRANSITIONS_STATES = (
    "stopping",
    "starting",
    "pending"
)


def fetch_state(compute_api, server):
    compute_api.module.debug("fetch_state of server: %s" % server["id"])
    response = compute_api.get(path="servers/%s" % server["id"])

    if response.status_code == 404:
        return "absent"

    if not response.ok:
        msg = 'Error during state fetching: (%s) %s' % (response.status_code, response.json)
        compute_api.module.fail_json(msg=msg)

    try:
        compute_api.module.debug("Server %s in state: %s" % (server["id"], response.json["server"]["state"]))
        return response.json["server"]["state"]
    except KeyError:
        compute_api.module.fail_json(msg="Could not fetch state in %s" % response.json)


def wait_to_complete_state_transition(compute_api, server):
    wait = compute_api.module.params["wait"]
    if not wait:
        return
    wait_timeout = compute_api.module.params["wait_timeout"]
    wait_sleep_time = compute_api.module.params["wait_sleep_time"]

    start = datetime.datetime.utcnow()
    end = start + datetime.timedelta(seconds=wait_timeout)
    while datetime.datetime.utcnow() < end:
        compute_api.module.debug("We are going to wait for the server to finish its transition")
        if fetch_state(compute_api, server) not in SCALEWAY_TRANSITIONS_STATES:
            compute_api.module.debug("It seems that the server is not in transition anymore.")
            compute_api.module.debug("Server in state: %s" % fetch_state(compute_api, server))
            break
        time.sleep(wait_sleep_time)
    else:
        compute_api.module.fail_json(msg="Server takes too long to finish its transition")


def public_ip_payload(compute_api, public_ip):
    # We don't want a public ip
    if public_ip in ("absent",):
        return {"dynamic_ip_required": False}

    # IP is only attached to the instance and is released as soon as the instance terminates
    if public_ip in ("dynamic", "allocated"):
        return {"dynamic_ip_required": True}

    # We check that the IP we want to attach exists, if so its ID is returned
    response = compute_api.get("ips")
    if not response.ok:
        msg = 'Error during public IP validation: (%s) %s' % (response.status_code, response.json)
        compute_api.module.fail_json(msg=msg)

    ip_list = []
    try:
        ip_list = response.json["ips"]
    except KeyError:
        compute_api.module.fail_json(msg="Error in getting the IP information from: %s" % response.json)

    lookup = [ip["id"] for ip in ip_list]
    if public_ip in lookup:
        return {"public_ip": public_ip}


def create_server(compute_api, server):
    compute_api.module.debug("Starting a create_server")
    target_server = None
    data = {"enable_ipv6": server["enable_ipv6"],
            "tags": server["tags"],
            "commercial_type": server["commercial_type"],
            "image": server["image"],
            "name": server["name"],
            "organization": server["organization"]
            }

    # Update optional parameters
    for optional_param in OPTIONAL_SERVER_ATTRIBUTES:
        if server.get(optional_param, None):
            data[optional_param] = server[optional_param]

    response = compute_api.post(path="servers", data=data)

    if not response.ok:
        msg = 'Error during server creation: (%s) %s' % (response.status_code, response.json)
        compute_api.module.fail_json(msg=msg)

    try:
        target_server = response.json["server"]
    except KeyError:
        compute_api.module.fail_json(msg="Error in getting the server information from: %s" % response.json)

    wait_to_complete_state_transition(compute_api=compute_api, server=target_server)

    return target_server


def restart_server(compute_api, server):
    return perform_action(compute_api=compute_api, server=server, action="reboot")


def stop_server(compute_api, server):
    return perform_action(compute_api=compute_api, server=server, action="poweroff")


def start_server(compute_api, server):
    return perform_action(compute_api=compute_api, server=server, action="poweron")


def perform_action(compute_api, server, action):
    response = compute_api.post(path="servers/%s/action" % server["id"],
                                data={"action": action})
    if not response.ok:
        msg = 'Error during server %s: (%s) %s' % (action, response.status_code, response.json)
        compute_api.module.fail_json(msg=msg)

    wait_to_complete_state_transition(compute_api=compute_api, server=server)

    return response


def remove_server(compute_api, server):
    compute_api.module.debug("Starting remove server strategy")
    response = compute_api.delete(path="servers/%s" % server["id"])
    if not response.ok:
        msg = 'Error during server deletion: (%s) %s' % (response.status_code, response.json)
        compute_api.module.fail_json(msg=msg)

    wait_to_complete_state_transition(compute_api=compute_api, server=server)

    return response


def present_strategy(compute_api, wished_server):
    compute_api.module.debug("Starting present strategy")
    changed = False
    query_results = find(compute_api=compute_api, wished_server=wished_server, per_page=1)

    if not query_results:
        changed = True
        if compute_api.module.check_mode:
            return changed, {"status": "A server would be created."}

        target_server = create_server(compute_api=compute_api, server=wished_server)
    else:
        target_server = query_results[0]

    if server_or_ip_should_be_changed(compute_api=compute_api, target_server=target_server,
                                           wished_server=wished_server):
        changed = True

        if compute_api.module.check_mode:
            return changed, {"status": "Server %s attributes would be changed." % target_server["id"]}

        target_server = server_change_attributes(compute_api=compute_api, target_server=target_server, wished_server=wished_server)
        target_server = server_change_ip_attribute(compute_api=compute_api, target_server=target_server, wished_server=wished_server)

    return changed, target_server


def absent_strategy(compute_api, wished_server):
    compute_api.module.debug("Starting absent strategy")
    changed = False
    target_server = None
    query_results = find(compute_api=compute_api, wished_server=wished_server, per_page=1)

    if not query_results:
        return changed, {"status": "Server already absent."}
    else:
        target_server = query_results[0]

    changed = True

    if compute_api.module.check_mode:
        return changed, {"status": "Server %s would be made absent." % target_server["id"]}

    # A server MUST be stopped to be deleted.
    while fetch_state(compute_api=compute_api, server=target_server) != "stopped":
        wait_to_complete_state_transition(compute_api=compute_api, server=target_server)
        response = stop_server(compute_api=compute_api, server=target_server)

        if not response.ok:
            err_msg = 'Error while stopping a server before removing it [{0}: {1}]'.format(response.status_code,
                                                                                           response.json)
            compute_api.module.fail_json(msg=err_msg)

        wait_to_complete_state_transition(compute_api=compute_api, server=target_server)

    response = remove_server(compute_api=compute_api, server=target_server)

    if not response.ok:
        err_msg = 'Error while removing server [{0}: {1}]'.format(response.status_code, response.json)
        compute_api.module.fail_json(msg=err_msg)

    return changed, {"status": "Server %s deleted" % target_server["id"]}


def running_strategy(compute_api, wished_server):
    compute_api.module.debug("Starting running strategy")
    changed = False
    query_results = find(compute_api=compute_api, wished_server=wished_server, per_page=1)

    if not query_results:
        changed = True
        if compute_api.module.check_mode:
            return changed, {"status": "A server would be created before being run."}

        target_server = create_server(compute_api=compute_api, server=wished_server)
    else:
        target_server = query_results[0]

    if server_or_ip_should_be_changed(compute_api=compute_api, target_server=target_server,
                                           wished_server=wished_server):
        changed = True

        if compute_api.module.check_mode:
            return changed, {"status": "Server %s attributes would be changed before running it." % target_server["id"]}

        target_server = server_change_attributes(compute_api=compute_api, target_server=target_server, wished_server=wished_server)
        target_server = server_change_ip_attribute(compute_api=compute_api, target_server=target_server, wished_server=wished_server)

    current_state = fetch_state(compute_api=compute_api, server=target_server)
    if current_state not in ("running", "starting"):
        compute_api.module.debug("running_strategy: Server in state: %s" % current_state)
        changed = True

        if compute_api.module.check_mode:
            return changed, {"status": "Server %s attributes would be changed." % target_server["id"]}

        response = start_server(compute_api=compute_api, server=target_server)
        if not response.ok:
            msg = 'Error while running server [{0}: {1}]'.format(response.status_code, response.json)
            compute_api.module.fail_json(msg=msg)

    return changed, target_server


def stop_strategy(compute_api, wished_server):
    compute_api.module.debug("Starting stop strategy")
    query_results = find(compute_api=compute_api, wished_server=wished_server, per_page=1)

    changed = False

    if not query_results:

        if compute_api.module.check_mode:
            return changed, {"status": "A server would be created before being stopped."}

        target_server = create_server(compute_api=compute_api, server=wished_server)
        changed = True
    else:
        target_server = query_results[0]

    compute_api.module.debug("stop_strategy: Servers are found.")

    if server_or_ip_should_be_changed(compute_api=compute_api, target_server=target_server,
                                           wished_server=wished_server):
        changed = True

        if compute_api.module.check_mode:
            return changed, {
                "status": "Server %s attributes would be changed before stopping it." % target_server["id"]}

        target_server = server_change_attributes(compute_api=compute_api, target_server=target_server, wished_server=wished_server)
        target_server = server_change_ip_attribute(compute_api=compute_api, target_server=target_server, wished_server=wished_server)

    wait_to_complete_state_transition(compute_api=compute_api, server=target_server)

    current_state = fetch_state(compute_api=compute_api, server=target_server)
    if current_state not in ("stopped",):
        compute_api.module.debug("stop_strategy: Server in state: %s" % current_state)

        changed = True

        if compute_api.module.check_mode:
            return changed, {"status": "Server %s would be stopped." % target_server["id"]}

        response = stop_server(compute_api=compute_api, server=target_server)
        compute_api.module.debug(response.json)
        compute_api.module.debug(response.ok)

        if not response.ok:
            msg = 'Error while stopping server [{0}: {1}]'.format(response.status_code, response.json)
            compute_api.module.fail_json(msg=msg)

    return changed, target_server


def restart_strategy(compute_api, wished_server):
    compute_api.module.debug("Starting restart strategy")
    changed = False
    query_results = find(compute_api=compute_api, wished_server=wished_server, per_page=1)

    if not query_results:
        changed = True
        if compute_api.module.check_mode:
            return changed, {"status": "A server would be created before being rebooted."}

        target_server = create_server(compute_api=compute_api, server=wished_server)
    else:
        target_server = query_results[0]

    if server_or_ip_should_be_changed(compute_api=compute_api, target_server=target_server,
                                           wished_server=wished_server):
        changed = True

        if compute_api.module.check_mode:
            return changed, {
                "status": "Server %s attributes would be changed before rebooting it." % target_server["id"]}

        target_server = server_change_attributes(compute_api=compute_api, target_server=target_server, wished_server=wished_server)
        target_server = server_change_ip_attribute(compute_api=compute_api, target_server=target_server, wished_server=wished_server)

    changed = True
    if compute_api.module.check_mode:
        return changed, {"status": "Server %s would be rebooted." % target_server["id"]}

    wait_to_complete_state_transition(compute_api=compute_api, server=target_server)

    if fetch_state(compute_api=compute_api, server=target_server) in ("running",):
        response = restart_server(compute_api=compute_api, server=target_server)
        wait_to_complete_state_transition(compute_api=compute_api, server=target_server)
        if not response.ok:
            msg = 'Error while restarting server that was running [{0}: {1}].'.format(response.status_code,
                                                                                      response.json)
            compute_api.module.fail_json(msg=msg)

    if fetch_state(compute_api=compute_api, server=target_server) in ("stopped",):
        response = restart_server(compute_api=compute_api, server=target_server)
        wait_to_complete_state_transition(compute_api=compute_api, server=target_server)
        if not response.ok:
            msg = 'Error while restarting server that was stopped [{0}: {1}].'.format(response.status_code,
                                                                                      response.json)
            compute_api.module.fail_json(msg=msg)

    return changed, target_server


state_strategy = {
    "present": present_strategy,
    "restarted": restart_strategy,
    "stopped": stop_strategy,
    "running": running_strategy,
    "absent": absent_strategy
}


def find(compute_api, wished_server, per_page=1):
    compute_api.module.debug("Getting inside find")
    # Only the name attribute is accepted in the Compute query API
    response = compute_api.get("servers", params={"name": wished_server["name"],
                                                  "per_page": per_page})

    if not response.ok:
        msg = 'Error during server search: (%s) %s' % (response.status_code, response.json)
        compute_api.module.fail_json(msg=msg)

    search_results = response.json["servers"]

    return search_results

OPTIONAL_SERVER_ATTRIBUTES = (
    "security_group",
    "dynamic_ip_required",
    "public_ip"
)

PATCH_MUTABLE_SERVER_ATTRIBUTES = (
    "ipv6",
    "tags",
    "name",
    "dynamic_ip_required",
    "security_group",
)


def server_or_ip_should_be_changed(compute_api, target_server, wished_server):
    compute_api.module.debug("Checking if server attributes should be changed")
    compute_api.module.debug("Current Server: %s" % target_server)
    compute_api.module.debug("Wished Server: %s" % wished_server)
    debug_dict = dict((x, (target_server[x], wished_server[x]))
                      for x in PATCH_MUTABLE_SERVER_ATTRIBUTES
                      if x in target_server and x in wished_server)
    compute_api.module.debug("Debug dict %s" % debug_dict)
    try:
        # Server attribute to change?
        for key in PATCH_MUTABLE_SERVER_ATTRIBUTES:
            if key in target_server and key in wished_server:
                # When you are working with dict, only ID matter as we ask user to put only the resource ID in the playbook
                if isinstance(target_server[key], dict) and wished_server[key] and "id" in target_server[key].keys(
                ) and target_server[key]["id"] != wished_server[key]:
                    return True
                # Handling other structure compare simply the two objects content
                elif not isinstance(target_server[key], dict) and target_server[key] != wished_server[key]:
                    return True

        # IP attribute to change?
        # Reserved IP to Reserved IP
        if "public_ip" in wished_server and target_server["public_ip"] and wished_server["public_ip"] != target_server["public_ip"]["id"]:
            return True

        # Reserved IP to Dynamic/Absent IP
        if target_server["public_ip"] and not target_server["public_ip"].get("dynamic") and "dynamic_ip_required" in wished_server:
            return True

        # Dynamic/Absent IP to Reserved one
        if "public_ip" in wished_server and (target_server["public_ip"] is None or (target_server["public_ip"] and target_server["public_ip"].get("dynamic"))):
            return True

        return False
    except AttributeError:
        compute_api.module.fail_json(msg="Error while checking if attributes should be changed")


def server_change_ip_attribute(compute_api, target_server, wished_server):
    compute_api.module.debug("Starting patching server ip attributes")
    # Update a reserved IP
    if "public_ip" in wished_server and target_server["public_ip"] and wished_server["public_ip"] != target_server["public_ip"]["id"]:
        # Free the current IP address
        compute_api.patch(path="ips/%s" % target_server["public_ip"]["id"], data={"server": None})
        # Attach new IP on the current server
        compute_api.patch(path="ips/%s" % wished_server["public_ip"], data={"server": target_server["id"]})

    # Reserved IP to Dynamic/Absent IP
    if target_server["public_ip"] and not target_server["public_ip"].get("dynamic", False) and "dynamic_ip_required" in wished_server:
        # Free the current IP address
        compute_api.patch(path="ips/%s" % target_server["public_ip"]["id"], data={"server": None})
        compute_api.patch(path="servers/%s" % target_server["public_ip"]["id"], data={"dynamic_ip_required": wished_server["dynamic_ip_required"]})

    # Dynamic/Absent IP to Reserved one
    if "public_ip" in wished_server and (target_server["public_ip"] is None or (target_server["public_ip"] and target_server["public_ip"].get("dynamic"))):
        # Attach the new IP to the current server
        compute_api.patch(path="ips/%s" % wished_server["public_ip"], data={"server": target_server["id"]})

    # Get modified server information
    response = compute_api.get(path="servers/%s" % target_server["id"])
    try:
        target_server = response.json["server"]
    except KeyError:
        compute_api.module.fail_json(msg="Error in getting the server information from: %s" % response.json)
    return target_server


def server_change_attributes(compute_api, target_server, wished_server):
    compute_api.module.debug("Starting patching server attributes")
    patch_payload = dict()

    for key in PATCH_MUTABLE_SERVER_ATTRIBUTES:
        if key in target_server and key in wished_server:
            # When you are working with dict, only ID matter as we ask user to put only the resource ID in the playbook
            if isinstance(target_server[key], dict) and "id" in target_server[key] and wished_server[key]:
                # Setting all key to current value except ID
                key_dict = dict((x, target_server[key][x]) for x in target_server[key].keys() if x != "id")
                # Setting ID to the user specified ID
                key_dict["id"] = wished_server[key]
                patch_payload[key] = key_dict
            elif not isinstance(target_server[key], dict):
                patch_payload[key] = wished_server[key]

    response = compute_api.patch(path="servers/%s" % target_server["id"],
                                 data=patch_payload)
    if not response.ok:
        msg = 'Error during server attributes patching: (%s) %s' % (response.status_code, response.json)
        compute_api.module.fail_json(msg=msg)

    try:
        target_server = response.json["server"]
    except KeyError:
        compute_api.module.fail_json(msg="Error in getting the server information from: %s" % response.json)

    wait_to_complete_state_transition(compute_api=compute_api, server=target_server)

    return target_server


def core(module):
    region = module.params["region"]
    wished_server = {
        "state": module.params["state"],
        "image": module.params["image"],
        "name": module.params["name"],
        "commercial_type": module.params["commercial_type"],
        "enable_ipv6": module.params["enable_ipv6"],
        "tags": module.params["tags"],
        "organization": module.params["organization"],
        "security_group": module.params["security_group"]
    }
    module.params['api_url'] = SCALEWAY_LOCATION[region]["api_endpoint"]

    compute_api = Scaleway(module=module)

    # IP parameters of the wished server depends on the configuration
    ip_payload = public_ip_payload(compute_api=compute_api, public_ip=module.params["public_ip"])
    wished_server.update(ip_payload)

    changed, summary = state_strategy[wished_server["state"]](compute_api=compute_api, wished_server=wished_server)
    module.exit_json(changed=changed, msg=summary)


def main():
    argument_spec = scaleway_argument_spec()
    argument_spec.update(dict(
        image=dict(required=True),
        name=dict(),
        region=dict(required=True, choices=SCALEWAY_LOCATION.keys()),
        commercial_type=dict(required=True, choices=SCALEWAY_COMMERCIAL_TYPES),
        enable_ipv6=dict(default=False, type="bool"),
        public_ip=dict(default="absent"),
        state=dict(choices=state_strategy.keys(), default='present'),
        tags=dict(type="list", default=[]),
        organization=dict(required=True),
        wait=dict(type="bool", default=False),
        wait_timeout=dict(type="int", default=300),
        wait_sleep_time=dict(type="int", default=3),
        security_group=dict(),
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    core(module)


if __name__ == '__main__':
    main()
