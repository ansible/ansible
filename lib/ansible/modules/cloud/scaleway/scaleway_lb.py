#!/usr/bin/python
#
# Scaleway Load-balancer management module
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
module: scaleway_lb
short_description: Scaleway load-balancer management module
version_added: "2.8"
author: Remy Leone (@sieben)
description:
    - "This module manages load-balancers on Scaleway."
extends_documentation_fragment: scaleway

options:

  name:
    description:
      - Name of the load-balancer
    required: true

  description:
    description:
      - Description of the load-balancer
    required: true

  organization_id:
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

  tags:
    description:
    - List of tags to apply to the load-balancer

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
- name: Create a load-balancer
  scaleway_lb:
    name: foobar
    state: present
    organization_id: 951df375-e094-4d26-97c1-ba548eeb9c42
    region: fr-par
    tags:
      - hello

- name: Delete a load-balancer
  scaleway_lb:
    name: foobar
    state: absent
    organization_id: 951df375-e094-4d26-97c1-ba548eeb9c42
    region: fr-par
'''

RETURNS = '''
{
   "scaleway_lb": {
      "backend_count": 0,
      "frontend_count": 0,
      "description": "Description of my load-balancer",
      "id": "00000000-0000-0000-0000-000000000000",
      "instances": [
         {
            "id": "00000000-0000-0000-0000-000000000000",
            "ip_address": "10.0.0.1",
            "region": "fr-par",
            "status": "ready"
         },
         {
            "id": "00000000-0000-0000-0000-000000000000",
            "ip_address": "10.0.0.2",
            "region": "fr-par",
            "status": "ready"
         }
      ],
      "ip": [
         {
            "id": "00000000-0000-0000-0000-000000000000",
            "ip_address": "192.168.0.1",
            "lb_id": "00000000-0000-0000-0000-000000000000",
            "region": "fr-par",
            "organization_id": "00000000-0000-0000-0000-000000000000",
            "reverse": ""
         }
      ],
      "name": "lb_ansible_test",
      "organization_id": "00000000-0000-0000-0000-000000000000",
      "region": "fr-par",
      "status": "ready",
      "tags": [
        "first_tag",
        "second_tag"
      ]
   }
}
'''

import datetime
import time
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.scaleway import SCALEWAY_REGIONS, SCALEWAY_ENDPOINT, scaleway_argument_spec, Scaleway

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
        "organization_id": wished_lb["organization_id"],
        "name": wished_lb["name"],
        "tags": wished_lb["tags"],
        "description": wished_lb["description"]
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


def wait_to_complete_state_transition(api, lb, force_wait=False):
    wait = api.module.params["wait"]
    if not (wait or force_wait):
        return
    wait_timeout = api.module.params["wait_timeout"]
    wait_sleep_time = api.module.params["wait_sleep_time"]

    start = datetime.datetime.utcnow()
    end = start + datetime.timedelta(seconds=wait_timeout)
    while datetime.datetime.utcnow() < end:
        api.module.debug("We are going to wait for the load-balancer to finish its transition")
        state = fetch_state(api, lb)
        if state in STABLE_STATES:
            api.module.debug("It seems that the load-balancer is not in transition anymore.")
            api.module.debug("load-balancer in state: %s" % fetch_state(api, lb))
            break
        time.sleep(wait_sleep_time)
    else:
        api.module.fail_json(msg="Server takes too long to finish its transition")


def lb_attributes_should_be_changed(target_lb, wished_lb):
    diff = dict((attr, wished_lb[attr]) for attr in MUTABLE_ATTRIBUTES if target_lb[attr] != wished_lb[attr])

    if diff:
        return dict((attr, wished_lb[attr]) for attr in MUTABLE_ATTRIBUTES)
    else:
        return diff


def present_strategy(api, wished_lb):
    changed = False

    response = api.get(path=api.api_path)
    if not response.ok:
        api.module.fail_json(msg='Error getting load-balancers [{0}: {1}]'.format(
            response.status_code, response.json['message']))

    lbs_list = response.json["lbs"]
    lb_lookup = dict((lb["name"], lb)
                     for lb in lbs_list)

    if wished_lb["name"] not in lb_lookup.keys():
        changed = True
        if api.module.check_mode:
            return changed, {"status": "A load-balancer would be created."}

        # Create Load-balancer
        api.warn(payload_from_wished_lb(wished_lb))
        creation_response = api.post(path=api.api_path,
                                     data=payload_from_wished_lb(wished_lb))

        if not creation_response.ok:
            msg = "Error during lb creation: %s: '%s' (%s)" % (creation_response.info['msg'],
                                                               creation_response.json['message'],
                                                               creation_response.json)
            api.module.fail_json(msg=msg)

        wait_to_complete_state_transition(api=api, lb=creation_response.json)
        response = api.get(path=api.api_path + "/%s" % creation_response.json["id"])
        return changed, response.json

    target_lb = lb_lookup[wished_lb["name"]]
    patch_payload = lb_attributes_should_be_changed(target_lb=target_lb,
                                                    wished_lb=wished_lb)

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

    wait_to_complete_state_transition(api=api, lb=target_lb)
    return changed, lb_patch_response.json


def absent_strategy(api, wished_lb):
    response = api.get(path=api.api_path)
    changed = False

    status_code = response.status_code
    lbs_json = response.json
    lbs_list = lbs_json["lbs"]

    if not response.ok:
        api.module.fail_json(msg='Error getting load-balancers [{0}: {1}]'.format(
            status_code, response.json['message']))

    lb_lookup = dict((lb["name"], lb)
                     for lb in lbs_list)
    if wished_lb["name"] not in lb_lookup.keys():
        return changed, {}

    target_lb = lb_lookup[wished_lb["name"]]
    changed = True
    if api.module.check_mode:
        return changed, {"status": "Load-balancer would be destroyed"}

    wait_to_complete_state_transition(api=api, lb=target_lb, force_wait=True)
    response = api.delete(path=api.api_path + "/%s" % target_lb["id"])
    if not response.ok:
        api.module.fail_json(msg='Error deleting load-balancer [{0}: {1}]'.format(
            response.status_code, response.json))

    wait_to_complete_state_transition(api=api, lb=target_lb)
    return changed, response.json


state_strategy = {
    "present": present_strategy,
    "absent": absent_strategy
}


def core(module):
    region = module.params["region"]
    wished_load_balancer = {
        "state": module.params["state"],
        "name": module.params["name"],
        "description": module.params["description"],
        "tags": module.params["tags"],
        "organization_id": module.params["organization_id"]
    }
    module.params['api_url'] = SCALEWAY_ENDPOINT
    api = Scaleway(module=module)
    api.api_path = "lbaas/v1beta1/regions/%s/lbs" % region

    changed, summary = state_strategy[wished_load_balancer["state"]](api=api,
                                                                     wished_lb=wished_load_balancer)
    module.exit_json(changed=changed, scaleway_lb=summary)


def main():
    argument_spec = scaleway_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        description=dict(required=True),
        region=dict(required=True, choices=SCALEWAY_REGIONS),
        state=dict(choices=state_strategy.keys(), default='present'),
        tags=dict(type="list", default=[]),
        organization_id=dict(required=True),
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
