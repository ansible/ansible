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
options:

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

  oauth_token:
    description:
     - Scaleway OAuth token.
    required: true

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
      - VC1S
      - VC1M
      - VC1L
      - X64-15GB
      - X64-30GB
      - X64-60GB
      - X64-120GB

  timeout:
    description:
    - Timeout for API calls
    required: false
    default: 30

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
'''

EXAMPLES = '''
- name: Create a server
  scaleway_compute:
    name: foobar
    state: present
    image: 89ee4018-f8c3-4dc4-a6b5-bca14f985ebe
    organization: 951df375-e094-4d26-97c1-ba548eeb9c42
    region: ams1
    commercial_type: VC1S
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
    commercial_type: VC1S
'''

RETURN = '''
'''

import datetime
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.six.moves.urllib.parse import quote as urlquote
from ansible.module_utils.scaleway import ScalewayAPI, SCALEWAY_LOCATION

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
    'VC1S',  # Starter X86-64 (2 cores) - 2GB
    'VC1M',  # Starter X86-64 (4 cores) - 4GB
    'VC1L',  # Starter X86-64 (6 cores) - 8GB
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


def create_server(compute_api, server):
    compute_api.module.debug("Starting a create_server")
    target_server = None
    response = compute_api.post(path="servers",
                                data={"enable_ipv6": server["enable_ipv6"],
                                      "tags": server["tags"],
                                      "commercial_type": server["commercial_type"],
                                      "image": server["image"],
                                      "name": server["name"],
                                      "organization": server["organization"]})

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

    if server_attributes_should_be_changed(compute_api=compute_api, target_server=target_server,
                                           wished_server=wished_server):
        changed = True

        if compute_api.module.check_mode:
            return changed, {"status": "Server %s attributes would be changed." % target_server["id"]}

        server_change_attributes(compute_api=compute_api, target_server=target_server, wished_server=wished_server)

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
    while not fetch_state(compute_api=compute_api, server=target_server) == "stopped":
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

    if server_attributes_should_be_changed(compute_api=compute_api, target_server=target_server,
                                           wished_server=wished_server):
        changed = True

        if compute_api.module.check_mode:
            return changed, {"status": "Server %s attributes would be changed before running it." % target_server["id"]}

        server_change_attributes(compute_api=compute_api, target_server=target_server, wished_server=wished_server)

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

    if server_attributes_should_be_changed(compute_api=compute_api, target_server=target_server,
                                           wished_server=wished_server):
        changed = True

        if compute_api.module.check_mode:
            return changed, {
                "status": "Server %s attributes would be changed before stopping it." % target_server["id"]}

        server_change_attributes(compute_api=compute_api, target_server=target_server, wished_server=wished_server)

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

    if server_attributes_should_be_changed(compute_api=compute_api,
                                           target_server=target_server,
                                           wished_server=wished_server):
        changed = True

        if compute_api.module.check_mode:
            return changed, {
                "status": "Server %s attributes would be changed before rebooting it." % target_server["id"]}

        server_change_attributes(compute_api=compute_api, target_server=target_server, wished_server=wished_server)

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
    url = 'servers?name=%s&per_page=%d' % (urlquote(wished_server["name"]), per_page)
    response = compute_api.get(url)

    if not response.ok:
        msg = 'Error during server search: (%s) %s' % (response.status_code, response.json)
        compute_api.module.fail_json(msg=msg)

    search_results = response.json["servers"]

    return search_results


PATCH_MUTABLE_SERVER_ATTRIBUTES = (
    "ipv6",
    "tags",
    "name",
    "dynamic_ip_required",
)


def server_attributes_should_be_changed(compute_api, target_server, wished_server):
    compute_api.module.debug("Checking if server attributes should be changed")
    compute_api.module.debug("Current Server: %s" % target_server)
    compute_api.module.debug("Wished Server: %s" % wished_server)
    debug_dict = dict((x, (target_server[x], wished_server[x]))
                      for x in PATCH_MUTABLE_SERVER_ATTRIBUTES
                      if x in target_server and x in wished_server)
    compute_api.module.debug("Debug dict %s" % debug_dict)

    try:
        return any([target_server[x] != wished_server[x]
                    for x in PATCH_MUTABLE_SERVER_ATTRIBUTES
                    if x in target_server and x in wished_server])
    except AttributeError:
        compute_api.module.fail_json(msg="Error while checking if attributes should be changed")


def server_change_attributes(compute_api, target_server, wished_server):
    compute_api.module.debug("Starting patching server attributes")
    patch_payload = dict((x, wished_server[x])
                         for x in PATCH_MUTABLE_SERVER_ATTRIBUTES
                         if x in wished_server and x in target_server)
    response = compute_api.patch(path="servers/%s" % target_server["id"],
                                 data=patch_payload)
    if not response.ok:
        msg = 'Error during server attributes patching: (%s) %s' % (response.status_code, response.json)
        compute_api.module.fail_json(msg=msg)

    wait_to_complete_state_transition(compute_api=compute_api, server=target_server)

    return response


def core(module):
    api_token = module.params['oauth_token']
    region = module.params["region"]
    wished_server = {
        "state": module.params["state"],
        "image": module.params["image"],
        "name": module.params["name"],
        "commercial_type": module.params["commercial_type"],
        "enable_ipv6": module.params["enable_ipv6"],
        "tags": module.params["tags"],
        "organization": module.params["organization"]
    }

    compute_api = ScalewayAPI(module=module,
                              headers={'X-Auth-Token': api_token},
                              base_url=SCALEWAY_LOCATION[region]["api_endpoint"])

    changed, summary = state_strategy[wished_server["state"]](compute_api=compute_api, wished_server=wished_server)
    module.exit_json(changed=changed, msg=summary)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            oauth_token=dict(
                no_log=True,
                # Support environment variable for Scaleway OAuth Token
                fallback=(env_fallback, ['SCW_TOKEN', 'SCW_API_KEY', 'SCW_OAUTH_TOKEN']),
                required=True,
            ),
            image=dict(required=True),
            name=dict(),
            region=dict(required=True, choices=SCALEWAY_LOCATION.keys()),
            commercial_type=dict(required=True, choices=SCALEWAY_COMMERCIAL_TYPES),
            enable_ipv6=dict(default=False, type="bool"),
            state=dict(choices=state_strategy.keys(), default='present'),
            tags=dict(type="list", default=[]),
            organization=dict(required=True),
            timeout=dict(type="int", default=30),
            wait=dict(type="bool", default=False),
            wait_timeout=dict(type="int", default=300),
            wait_sleep_time=dict(type="int", default=3),
        ),
        supports_check_mode=True,
    )

    core(module)


if __name__ == '__main__':
    main()
