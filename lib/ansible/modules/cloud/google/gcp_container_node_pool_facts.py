#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Google
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# ----------------------------------------------------------------------------
#
#     ***     AUTO GENERATED CODE    ***    AUTO GENERATED CODE     ***
#
# ----------------------------------------------------------------------------
#
#     This file is automatically generated by Magic Modules and manual
#     changes will be clobbered when the file is regenerated.
#
#     Please read more about how to change this file at
#     https://www.github.com/GoogleCloudPlatform/magic-modules
#
# ----------------------------------------------------------------------------

from __future__ import absolute_import, division, print_function

__metaclass__ = type

################################################################################
# Documentation
################################################################################

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ["preview"], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: gcp_container_node_pool_facts
description:
- Gather facts for GCP NodePool
short_description: Gather facts for GCP NodePool
version_added: 2.8
author: Google Inc. (@googlecloudplatform)
requirements:
- python >= 2.6
- requests >= 2.18.4
- google-auth >= 1.3.0
options:
  cluster:
    description:
    - The cluster this node pool belongs to.
    - 'This field represents a link to a Cluster resource in GCP. It can be specified
      in two ways. First, you can place in the name of the resource here as a string
      Alternatively, you can add `register: name-of-resource` to a gcp_container_cluster
      task and then set this cluster field to "{{ name-of-resource }}"'
    required: true
extends_documentation_fragment: gcp
'''

EXAMPLES = '''
- name:  a node pool facts
  gcp_container_node_pool_facts:
      cluster: "{{ cluster }}"
      project: test_project
      auth_kind: serviceaccount
      service_account_file: "/tmp/auth.pem"
'''

RETURN = '''
items:
  description: List of items
  returned: always
  type: complex
  contains:
    name:
      description:
      - The name of the node pool.
      returned: success
      type: str
    config:
      description:
      - The node configuration of the pool.
      returned: success
      type: complex
      contains:
        machineType:
          description:
          - The name of a Google Compute Engine machine type (e.g.
          - n1-standard-1). If unspecified, the default machine type is n1-standard-1.
          returned: success
          type: str
        diskSizeGb:
          description:
          - Size of the disk attached to each node, specified in GB. The smallest
            allowed disk size is 10GB. If unspecified, the default disk size is 100GB.
          returned: success
          type: int
        oauthScopes:
          description:
          - The set of Google API scopes to be made available on all of the node VMs
            under the "default" service account.
          - 'The following scopes are recommended, but not required, and by default
            are not included: U(https://www.googleapis.com/auth/compute) is required
            for mounting persistent storage on your nodes.'
          - U(https://www.googleapis.com/auth/devstorage.read_only) is required for
            communicating with gcr.io (the Google Container Registry).
          - If unspecified, no scopes are added, unless Cloud Logging or Cloud Monitoring
            are enabled, in which case their required scopes will be added.
          returned: success
          type: list
        serviceAccount:
          description:
          - The Google Cloud Platform Service Account to be used by the node VMs.
            If no Service Account is specified, the "default" service account is used.
          returned: success
          type: str
        metadata:
          description:
          - The metadata key/value pairs assigned to instances in the cluster.
          - 'Keys must conform to the regexp [a-zA-Z0-9-_]+ and be less than 128 bytes
            in length. These are reflected as part of a URL in the metadata server.
            Additionally, to avoid ambiguity, keys must not conflict with any other
            metadata keys for the project or be one of the four reserved keys: "instance-template",
            "kube-env", "startup-script", and "user-data" Values are free-form strings,
            and only have meaning as interpreted by the image running in the instance.
            The only restriction placed on them is that each value''s size must be
            less than or equal to 32 KB.'
          - The total size of all keys and values must be less than 512 KB.
          - 'An object containing a list of "key": value pairs.'
          - 'Example: { "name": "wrench", "mass": "1.3kg", "count": "3" }.'
          returned: success
          type: dict
        imageType:
          description:
          - The image type to use for this node. Note that for a given image type,
            the latest version of it will be used.
          returned: success
          type: str
        labels:
          description:
          - 'The map of Kubernetes labels (key/value pairs) to be applied to each
            node. These will added in addition to any default label(s) that Kubernetes
            may apply to the node. In case of conflict in label keys, the applied
            set may differ depending on the Kubernetes version -- it''s best to assume
            the behavior is undefined and conflicts should be avoided. For more information,
            including usage and the valid values, see: U(http://kubernetes.io/v1.1/docs/user-guide/labels.html)
            An object containing a list of "key": value pairs.'
          - 'Example: { "name": "wrench", "mass": "1.3kg", "count": "3" }.'
          returned: success
          type: dict
        localSsdCount:
          description:
          - The number of local SSD disks to be attached to the node.
          - 'The limit for this value is dependant upon the maximum number of disks
            available on a machine per zone. See: U(https://cloud.google.com/compute/docs/disks/local-ssd#local_ssd_limits)
            for more information.'
          returned: success
          type: int
        tags:
          description:
          - The list of instance tags applied to all nodes. Tags are used to identify
            valid sources or targets for network firewalls and are specified by the
            client during cluster or node pool creation. Each tag within the list
            must comply with RFC1035.
          returned: success
          type: list
        preemptible:
          description:
          - 'Whether the nodes are created as preemptible VM instances. See: U(https://cloud.google.com/compute/docs/instances/preemptible)
            for more information about preemptible VM instances.'
          returned: success
          type: bool
    initialNodeCount:
      description:
      - The initial node count for the pool. You must ensure that your Compute Engine
        resource quota is sufficient for this number of instances. You must also have
        available firewall and routes quota.
      returned: success
      type: int
    version:
      description:
      - The version of the Kubernetes of this node.
      returned: success
      type: str
    autoscaling:
      description:
      - Autoscaler configuration for this NodePool. Autoscaler is enabled only if
        a valid configuration is present.
      returned: success
      type: complex
      contains:
        enabled:
          description:
          - Is autoscaling enabled for this node pool.
          returned: success
          type: bool
        minNodeCount:
          description:
          - Minimum number of nodes in the NodePool. Must be >= 1 and <= maxNodeCount.
          returned: success
          type: int
        maxNodeCount:
          description:
          - Maximum number of nodes in the NodePool. Must be >= minNodeCount.
          - There has to enough quota to scale up the cluster.
          returned: success
          type: int
    management:
      description:
      - Management configuration for this NodePool.
      returned: success
      type: complex
      contains:
        autoUpgrade:
          description:
          - A flag that specifies whether node auto-upgrade is enabled for the node
            pool. If enabled, node auto-upgrade helps keep the nodes in your node
            pool up to date with the latest release version of Kubernetes.
          returned: success
          type: bool
        autoRepair:
          description:
          - A flag that specifies whether the node auto-repair is enabled for the
            node pool. If enabled, the nodes in this node pool will be monitored and,
            if they fail health checks too many times, an automatic repair action
            will be triggered.
          returned: success
          type: bool
        upgradeOptions:
          description:
          - Specifies the Auto Upgrade knobs for the node pool.
          returned: success
          type: complex
          contains:
            autoUpgradeStartTime:
              description:
              - This field is set when upgrades are about to commence with the approximate
                start time for the upgrades, in RFC3339 text format.
              returned: success
              type: str
            description:
              description:
              - This field is set when upgrades are about to commence with the description
                of the upgrade.
              returned: success
              type: str
    cluster:
      description:
      - The cluster this node pool belongs to.
      returned: success
      type: str
'''

################################################################################
# Imports
################################################################################
from ansible.module_utils.gcp_utils import navigate_hash, GcpSession, GcpModule, GcpRequest, replace_resource_dict
import json

################################################################################
# Main
################################################################################


def main():
    module = GcpModule(argument_spec=dict(cluster=dict(required=True)))

    if not module.params['scopes']:
        module.params['scopes'] = ['https://www.googleapis.com/auth/cloud-platform']

    items = fetch_list(module, collection(module))
    if items.get('nodePools'):
        items = items.get('nodePools')
    else:
        items = []
    return_value = {'items': items}
    module.exit_json(**return_value)


def collection(module):
    res = {'project': module.params['project'], 'location': module.params['location'], 'cluster': replace_resource_dict(module.params['cluster'], 'name')}
    return "https://container.googleapis.com/v1/projects/{project}/zones/{location}/clusters/{cluster}/nodePools".format(**res)


def fetch_list(module, link):
    auth = GcpSession(module, 'container')
    response = auth.get(link)
    return return_if_object(module, response)


def return_if_object(module, response):
    # If not found, return nothing.
    if response.status_code == 404:
        return None

    # If no content, return nothing.
    if response.status_code == 204:
        return None

    try:
        module.raise_for_status(response)
        result = response.json()
    except getattr(json.decoder, 'JSONDecodeError', ValueError) as inst:
        module.fail_json(msg="Invalid JSON response with error: %s" % inst)

    if navigate_hash(result, ['error', 'errors']):
        module.fail_json(msg=navigate_hash(result, ['error', 'errors']))

    return result


if __name__ == "__main__":
    main()
