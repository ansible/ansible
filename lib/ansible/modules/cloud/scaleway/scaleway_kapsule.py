#!/usr/bin/python
#
# Scaleway Kubernetes as a Service management module
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
module: scaleway_k8s
short_description: Scaleway Kubernetes as a Service management module
version_added: "2.8"
author: Remy Leone (@sieben)
description:
    - This module manages managed Kubernetes on Scaleway
      U(https://developer.scaleway.com)
extends_documentation_fragment: scaleway

options:
  name:
    description: Name of the cluster

  state:
    description:
     - Indicate desired state of the Kubernetes cluster.
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

  cni:
    description: k8s CNI to use
    choices:
      - calico
      - flannel
      - weave
    default: flannel

  ingress:
    description: Cluster Ingress
    default: none
    choices:
      - nginx
      - none
      - traefik

  description:
    description: Description for the k8s cluster

  default_pool_autoscaling:
    description: Enable/Disable autoscaling
    type: boolean

  default_pool_max_size:
    description: Maximal size of the default pool
    type: int

  default_pool_min_size:
    description: Minimal size of the default pool
    type: int

  default_pool_size:
    description: Current size of the default pool
    type: int

  default_pool_commercial_type:
    description: Commercial type of pool resources
    default: start1s
    choices:
      - start1s
      - start1m
      - start1l

  dashboard:
    description: Enable/disable Kubernetes dashboard deployment
    type: boolean
    required: true

  version:
    description: k8s version to deploy

  tags:
    description: List of tags to apply to the cluster
    type: list
    default []
'''

EXAMPLES = '''
  - name: Create a k8s cluster
    scaleway_k8s:
      organization: '{{ scw_org }}'
      state: present
      region: par1
    register: k8s_cluster_creation_task
'''

RETURN = '''
data:
    description: This is only present when C(state=present)
    returned: when C(state=present)
    type: dict
    sample: {
      "scaleway_k8s": [
        {
            "organization": "951df375-e094-4d26-97c1-ba548eeb9c42",
            "id": "dd9e8df6-6775-4863-b517-e0b0ee3d7477",
        }
    ]
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.scaleway import SCALEWAY_LOCATION, scaleway_argument_spec, Scaleway

SUPPORTED_COMMERCIAL_TYPE = (
    # Virtual X86-64 compute instance
    'start1s',  # Starter X86-64 (2 cores) - 2GB - 50 GB NVMe
    'start1m',  # Starter X86-64 (4 cores) - 4GB - 100 GB NVMe
    'start1l',  # Starter X86-64 (8 cores) - 8GB - 200 GB NVMe
)

CLUSTER_ENDPOINT = '/kapsule/v1beta1/clusters'


def present_strategy(api, wished_cluster):
    changed = False

    response = api.get(CLUSTER_ENDPOINT)
    if not response.ok:
        api.module.fail_json(msg='Error getting Kubernetes cluster [{0}: {1}]'.format(
            response.status_code, response.json['message']))

    cluster_list = response.json["clusters"]
    cluster_lookup = dict((cluster["name"], cluster)
                          for cluster in cluster_list)

    if wished_cluster["name"] not in cluster_lookup.keys():
        changed = True
        if api.module.check_mode:
            return changed, {"status": "A cluster would be created."}

        # Create cluster
        api.warn(wished_cluster)
        creation_response = api.post(CLUSTER_ENDPOINT,
                                     data=wished_cluster)

        if not creation_response.ok:
            msg = "Error during cluster creation: %s: '%s' (%s)" % (creation_response.info['msg'],
                                                                    creation_response.json['message'],
                                                                    creation_response.json)
            api.module.fail_json(msg=msg)
        return changed, creation_response.json

    # target_ip = ip_lookup[wished_cluster["id"]]
    # patch_payload = ip_attributes_should_be_changed(api=api, target_ip=target_ip, wished_ip=wished_ip)
    #
    # if not patch_payload:
    #     return changed, target_ip
    #
    # changed = True
    # if api.module.check_mode:
    #     return changed, {"status": "IP attributes would be changed."}
    #
    # ip_patch_response = api.patch(path="ips/%s" % target_ip["id"],
    #                               data=patch_payload)
    #
    # if not ip_patch_response.ok:
    #     api.module.fail_json(msg='Error during IP attributes update: [{0}: {1}]'.format(
    #         ip_patch_response.status_code, ip_patch_response.json['message']))
    #
    # return changed, ip_patch_response.json["ip"]

    return changed, response.json


def absent_strategy(api, wished_cluster):
    changed = False

    response = api.get(CLUSTER_ENDPOINT)
    if not response.ok:
        api.module.fail_json(msg='Error getting Kubernetes cluster [{0}: {1}]'.format(
            response.status_code, response.json['message']))

    cluster_list = response.json["clusters"]
    cluster_lookup = dict((cluster["name"], cluster)
                          for cluster in cluster_list)

    if wished_cluster["name"] not in cluster_lookup.keys():
        return changed, {}

    changed = True
    if api.module.check_mode:
        return changed, {"status": "Cluster %s would be destroyed" % wished_cluster["name"]}

    response = api.delete(CLUSTER_ENDPOINT + '/' + wished_cluster["id"])
    if not response.ok:
        api.module.fail_json(msg='Error deleting cluster [{0}: {1}]'.format(
            response.status_code, response.json))

    return changed, response.json


def core(module):
    region = module.params["region"]
    wished_cluster = {
        "name": module.params["name"],
        "tags": module.params["tags"],
        "cni": module.params["cni"],
        "ingress": module.params["ingress"],
        "description": module.params["description"],
        "organization_id": module.params["organization_id"],
        "version": module.params["version"]
    }
    module.params['api_url'] = SCALEWAY_LOCATION[region]["api_endpoint"]

    api = Scaleway(module=module)

    if module.params["state"] == "absent":
        changed, summary = absent_strategy(api=api, wished_cluster=wished_cluster)
    else:
        changed, summary = present_strategy(api=api, wished_cluster=wished_cluster)
    module.exit_json(changed=changed, scaleway_kapsule=summary)


def main():
    argument_spec = scaleway_argument_spec()
    argument_spec.update(dict(
        cni=dict(choices=["calico", "flannel", "weave"], default="flannel"),
        dashboard=dict(type="boolean"),
        default_pool_autoscaling=dict(),
        default_pool_commercial_type=dict(choices=SUPPORTED_COMMERCIAL_TYPE),
        default_pool_max_size=dict(),
        default_pool_min_size=dict(),
        default_pool_size=dict(),
        description=dict(),
        ingress=dict(choices=["nginx", "none", "traefik"], default="none"),
        name=dict(required=True),
        organization_id=dict(required=True),
        region=dict(required=True, choices=SCALEWAY_LOCATION.keys()),
        state=dict(choices=["present", "absent"], default='present'),
        tags=dict(type="list", default=[]),
        version=dict(),
        wait=dict(type="bool", default=False),
        wait_timeout=dict(type="int", default=300),
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    core(module)


if __name__ == '__main__':
    main()
