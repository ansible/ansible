#!/usr/bin/python
#
# Scaleway IP management module
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
module: scaleway_ip
short_description: Scaleway IP management module
version_added: "2.8"
author: Remy Leone (@sieben)
description:
    - This module manages IP on Scaleway account
      U(https://developer.scaleway.com)
extends_documentation_fragment: scaleway

options:
  state:
    description:
     - Indicate desired state of the IP.
    default: present
    choices:
      - present
      - absent

  organization:
    description:
      - Scaleway organization identifier
    required: true

  region:
    description:
     - Scaleway region to use (for example par1).
    required: true
    choices:
      - ams1
      - EMEA-NL-EVS
      - par1
      - EMEA-FR-PAR1

  id:
    description:
    - id of the Scaleway IP (UUID)

  server:
    description:
    - id of the server you want to attach an IP to.
    - To unattach an IP don't specify this option

  reverse:
    description:
    - Reverse to assign to the IP
'''

EXAMPLES = '''
  - name: Create an IP
    scaleway_ip:
      organization: '{{ scw_org }}'
      state: present
      region: par1
    register: ip_creation_task

  - name: Make sure IP deleted
    scaleway_ip:
      id: '{{ ip_creation_task.scaleway_ip.id }}'
      state: absent
      region: par1

'''

RETURN = '''
data:
    description: This is only present when C(state=present)
    returned: when C(state=present)
    type: dict
    sample: {
      "ips": [
        {
            "organization": "951df375-e094-4d26-97c1-ba548eeb9c42",
            "reverse": null,
            "id": "dd9e8df6-6775-4863-b517-e0b0ee3d7477",
            "server": {
                "id": "3f1568ca-b1a2-4e98-b6f7-31a0588157f1",
                "name": "ansible_tuto-1"
            },
            "address": "212.47.232.136"
        }
    ]
    }
'''

from ansible.module_utils.scaleway import SCALEWAY_LOCATION, scaleway_argument_spec, Scaleway
from ansible.module_utils.basic import AnsibleModule


def ip_attributes_should_be_changed(api, target_ip, wished_ip):
    patch_payload = {}

    if target_ip["reverse"] != wished_ip["reverse"]:
        patch_payload["reverse"] = wished_ip["reverse"]

    # IP is assigned to a server
    if target_ip["server"] is None and wished_ip["server"]:
        patch_payload["server"] = wished_ip["server"]

    # IP is unassigned to a server
    try:
        if target_ip["server"]["id"] and wished_ip["server"] is None:
            patch_payload["server"] = wished_ip["server"]
    except (TypeError, KeyError):
        pass

    # IP is migrated between 2 different servers
    try:
        if target_ip["server"]["id"] != wished_ip["server"]:
            patch_payload["server"] = wished_ip["server"]
    except (TypeError, KeyError):
        pass

    return patch_payload


def payload_from_wished_ip(wished_ip):
    return dict(
        (k, v)
        for k, v in wished_ip.items()
        if k != 'id' and v is not None
    )


def present_strategy(api, wished_ip):
    changed = False

    response = api.get('ips')
    if not response.ok:
        api.module.fail_json(msg='Error getting IPs [{0}: {1}]'.format(
            response.status_code, response.json['message']))

    ips_list = response.json["ips"]
    ip_lookup = dict((ip["id"], ip)
                     for ip in ips_list)

    if wished_ip["id"] not in ip_lookup.keys():
        changed = True
        if api.module.check_mode:
            return changed, {"status": "An IP would be created."}

        # Create IP
        creation_response = api.post('/ips',
                                     data=payload_from_wished_ip(wished_ip))

        if not creation_response.ok:
            msg = "Error during ip creation: %s: '%s' (%s)" % (creation_response.info['msg'],
                                                               creation_response.json['message'],
                                                               creation_response.json)
            api.module.fail_json(msg=msg)
        return changed, creation_response.json["ip"]

    target_ip = ip_lookup[wished_ip["id"]]
    patch_payload = ip_attributes_should_be_changed(api=api, target_ip=target_ip, wished_ip=wished_ip)

    if not patch_payload:
        return changed, target_ip

    changed = True
    if api.module.check_mode:
        return changed, {"status": "IP attributes would be changed."}

    ip_patch_response = api.patch(path="ips/%s" % target_ip["id"],
                                  data=patch_payload)

    if not ip_patch_response.ok:
        api.module.fail_json(msg='Error during IP attributes update: [{0}: {1}]'.format(
            ip_patch_response.status_code, ip_patch_response.json['message']))

    return changed, ip_patch_response.json["ip"]


def absent_strategy(api, wished_ip):
    response = api.get('ips')
    changed = False

    status_code = response.status_code
    ips_json = response.json
    ips_list = ips_json["ips"]

    if not response.ok:
        api.module.fail_json(msg='Error getting IPs [{0}: {1}]'.format(
            status_code, response.json['message']))

    ip_lookup = dict((ip["id"], ip)
                     for ip in ips_list)
    if wished_ip["id"] not in ip_lookup.keys():
        return changed, {}

    changed = True
    if api.module.check_mode:
        return changed, {"status": "IP would be destroyed"}

    response = api.delete('/ips/' + wished_ip["id"])
    if not response.ok:
        api.module.fail_json(msg='Error deleting IP [{0}: {1}]'.format(
            response.status_code, response.json))

    return changed, response.json


def core(module):
    wished_ip = {
        "organization": module.params['organization'],
        "reverse": module.params["reverse"],
        "id": module.params["id"],
        "server": module.params["server"]
    }

    region = module.params["region"]
    module.params['api_url'] = SCALEWAY_LOCATION[region]["api_endpoint"]

    api = Scaleway(module=module)
    if module.params["state"] == "absent":
        changed, summary = absent_strategy(api=api, wished_ip=wished_ip)
    else:
        changed, summary = present_strategy(api=api, wished_ip=wished_ip)
    module.exit_json(changed=changed, scaleway_ip=summary)


def main():
    argument_spec = scaleway_argument_spec()
    argument_spec.update(dict(
        state=dict(default='present', choices=['absent', 'present']),
        organization=dict(required=True),
        server=dict(),
        reverse=dict(),
        region=dict(required=True, choices=SCALEWAY_LOCATION.keys()),
        id=dict()
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    core(module)


if __name__ == '__main__':
    main()
