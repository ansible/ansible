#!/usr/bin/python
#
# Scaleway Load-balancer backend management module
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
module: scaleway_lb_back
short_description: Scaleway load-balancer backend management module
version_added: "2.8"
author: Remy Leone (@sieben)
description:
    - "This module manages load-balancers backend on Scaleway."
extends_documentation_fragment: scaleway

options:

  name:
    description:
      - Name of the load-balancer backend

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

  region:
    description:
    - Scaleway zone
    required: true
    choices:
      - nl-ams
      - fr-par

  forward_port:
    description:
      - User sessions will be forwarded to this port of backend servers

  forward_port_algorithm:
    description:
      - Load balancing algorithm:
      - Round-Robin: Equal share
      - leastconn: Least amount of TCP connection
    choices:
      - leastconn
      - roundrobin

  forward_protocol:
    description:
      - Backend protocol
    choices:
      - tcp
      - http
    default:
      - tcp

  on_marked_down_action:
    description:
      - Modify what occurs when a backend server is marked down
    choices:
      - on_marked_down_action_none
      - shutdown_sessions

  send_proxy_v2:
    description:
    - Enables PROXY protocol version 2 (must be supported by backend servers)
    type: bool
    default: no

  server_ip:
    description:
    - Backend server IP addresses list (IPv4 or IPv6)

  sticky_sessions:
    description:
    - Enables cookie-based session persistence
    default: none
    choices:
    - cookie
    - none
    - table (Will match on IP)

  sticky_sessions_cookie_name:
    description:
    - Cookie name for sticky sessions

  timeout_connect:
    description:
    - Maximum initial server connection establishment time in milliseconds

  timeout_server:
    description:
    - Maximum server connection inactivity time in milliseconds

  timeout_tunnel:
    description:
    - Maximum tunnel inactivity time in milliseconds

  wait:
    description:
    - Wait for the load-balancer to reach its desired state before returning.
    type: bool
    default: 'no'

  wait_timeout:
    description:
    - Time to wait for the load-balancer to reach the expected state
    required: false
    default: 300

  wait_sleep_time:
    description:
    - Time to wait before every attempt to check the state of the load-balancer
    required: false
    default: 3
'''

EXAMPLES = '''
'''

RETURNS = '''
'''

import datetime
import time
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.scaleway import SCALEWAY_NEW_LOCATION, scaleway_argument_spec, Scaleway

STABLE_STATES = (
    "ready",
    "absent"
)

MUTABLE_ATTRIBUTES = (
    "name",
    "description"
)


def payload_from_wished_lb(wished_lb):
    return {
        # "organization_id": wished_lb["organization_id"],
        "name": wished_lb["name"],
    }


def fetch_state(api, lb):
    api.module.debug("fetch_state of load-balancer: %s" % lb["id"])
    response = api.get(path=api.api_path + "/%s" % lb["id"])

    if response.status_code == 404:
        return "absent"

    if not response.ok:
        msg = 'Error during state fetching: (%s) %s' % (response.status_code, response.json)
        api.module.fail_json(msg=msg)

    try:
        api.module.debug("Load-balancer %s in state: %s" % (lb["id"], response.json["status"]))
        return response.json["status"]
    except KeyError:
        api.module.fail_json(msg="Could not fetch state in %s" % response.json)


def wait_to_complete_state_transition(api, lb_backend, force_wait=False):
    wait = api.module.params["wait"]
    if not (wait or force_wait):
        return
    wait_timeout = api.module.params["wait_timeout"]
    wait_sleep_time = api.module.params["wait_sleep_time"]

    start = datetime.datetime.utcnow()
    end = start + datetime.timedelta(seconds=wait_timeout)
    while datetime.datetime.utcnow() < end:
        api.module.debug("We are going to wait for the load-balancer to finish its transition")
        state = fetch_state(api, lb_backend)
        if state in STABLE_STATES:
            api.module.debug("It seems that the load-balancer is not in transition anymore.")
            api.module.debug("load-balancer in state: %s" % fetch_state(api, lb_backend))
            break
        time.sleep(wait_sleep_time)
    else:
        api.module.fail_json(msg="Server takes too long to finish its transition")


def lb_attributes_should_be_changed(target_lb_backend, wished_lb_backend):
    diff = {
        attr: wished_lb_backend[attr] for attr in MUTABLE_ATTRIBUTES if target_lb_backend[attr] != wished_lb_backend[attr]
    }
    if diff:
        return {attr: wished_lb_backend[attr] for attr in MUTABLE_ATTRIBUTES}
    else:
        return diff


def present_strategy(api, wished_lb_backend):
    changed = False

    response = api.get(path=api.api_path)
    if not response.ok:
        api.module.fail_json(msg='Error getting load-balancers [{0}: {1}]'.format(
            response.status_code, response.json['message']))

    lbs_list = response.json["backends"]
    lb_lookup = dict((lb["name"], lb)
                     for lb in lbs_list)

    if wished_lb_backend["name"] not in lb_lookup.keys():
        changed = True
        if api.module.check_mode:
            return changed, {"status": "A load-balancer would be created."}

        # Create Load-balancer
        api.warn(payload_from_wished_lb(wished_lb_backend))
        creation_response = api.post(path=api.api_path,
                                     data=payload_from_wished_lb(wished_lb_backend))

        if not creation_response.ok:
            msg = "Error during lb creation: %s: '%s' (%s)" % (creation_response.info['msg'],
                                                               creation_response.json['message'],
                                                               creation_response.json)
            api.module.fail_json(msg=msg)

        wait_to_complete_state_transition(api=api, lb_backend=creation_response.json)
        response = api.get(path=api.api_path + "/%s" % creation_response.json["id"])
        return changed, response.json

    target_lb = lb_lookup[wished_lb_backend["name"]]
    patch_payload = lb_attributes_should_be_changed(target_lb_backend=target_lb,
                                                    wished_lb_backend=wished_lb_backend)

    if not patch_payload:
        return changed, target_lb

    changed = True
    if api.module.check_mode:
        return changed, {"status": "Load-balancer attributes would be changed."}

    lb_patch_response = api.put(path=api.api_path + "/%s" % target_lb["id"],
                                data=patch_payload)

    if not lb_patch_response.ok:
        api.module.fail_json(msg='Error during load-balancer attributes update: [{0}: {1}]'.format(
            lb_patch_response.status_code, lb_patch_response.json['message']))

    wait_to_complete_state_transition(api=api, lb_backend=target_lb)
    return changed, lb_patch_response.json


def absent_strategy(api, wished_lb_backend):
    response = api.get(path=api.api_path)
    changed = False

    status_code = response.status_code
    lbs_json = response.json
    lbs_list = lbs_json["backends"]

    if not response.ok:
        api.module.fail_json(msg='Error getting load-balancers [{0}: {1}]'.format(
            status_code, response.json['message']))

    lb_lookup = dict((lb["name"], lb)
                     for lb in lbs_list)
    if wished_lb_backend["name"] not in lb_lookup.keys():
        return changed, {}

    target_lb = lb_lookup[wished_lb_backend["name"]]
    changed = True
    if api.module.check_mode:
        return changed, {"status": "Load-balancer would be destroyed"}

    wait_to_complete_state_transition(api=api, lb_backend=target_lb, force_wait=True)
    response = api.delete(path=api.api_path + "/%s" % target_lb["id"])
    if not response.ok:
        api.module.fail_json(msg='Error deleting load-balancer [{0}: {1}]'.format(
            response.status_code, response.json))

    wait_to_complete_state_transition(api=api, lb_backend=target_lb)
    return changed, response.json


state_strategy = {
    "present": present_strategy,
    "absent": absent_strategy
}


def core(module):
    region = module.params["region"]
    lb_id = module.params["lb_id"]
    wished_load_balancer_back = {
        "name": module.params["name"],
        "state": module.params["state"],
        "lb_id": module.params["lb_id"],
        "forward_port": module.params["forward_port"],
        "forward_protocol": module.params["forward_protocol"],
        "forward_port_algorithm": module.params["forward_port_algorithm"],
        "sticky_sessions": module.params["sticky_sessions"],
        "timeout_connect": module.params["timeout_connect"],
        "timeout_server": module.params["timeout_server"],
        "timeout_tunnel": module.params["timeout_tunnel"]
    }
    module.params['api_url'] = SCALEWAY_NEW_LOCATION[region]["api_endpoint"]
    api = Scaleway(module=module)
    api.api_path = "lbaas/v1beta1/regions/%s/lbs/%s/backends" % (region, lb_id)

    changed, summary = state_strategy[wished_load_balancer_back["state"]](api=api,
                                                                          wished_lb_backend=wished_load_balancer_back)
    module.exit_json(changed=changed, scaleway_lb=summary)


def main():
    argument_spec = scaleway_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        state=dict(choices=state_strategy.keys(), default='present'),
        lb_id=dict(required=True),
        forward_port=dict(required=True, type='int'),
        forward_protocol=dict(choices=["http", "tcp"], default="tcp"),
        forward_port_algorithm=dict(choices=["roundrobin", "leastconn"], default="roundrobin"),
        region=dict(required=True, choices=SCALEWAY_NEW_LOCATION.keys()),
        sticky_sessions=dict(choices=["cookie", "none", "table"], default="none"),
        timeout_connect=dict(type="int"),
        timeout_server=dict(type="int"),
        timeout_tunnel=dict(type="int"),
        wait=dict(type="bool", default=False),
        wait_timeout=dict(type="int", default=300),
        wait_sleep_time=dict(type="int", default=3),
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    core(module)


if __name__ == '__main__':
    main()
