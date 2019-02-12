#!/usr/bin/python

# Copyright (c) 2018 Catalyst IT Ltd.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_coe_cluster
short_description: Add/Remove COE cluster from OpenStack Cloud
extends_documentation_fragment: openstack
version_added: "2.8"
author: "Feilong Wang (@flwang)"
description:
   - Add or Remove COE cluster from the OpenStack Container Infra service.
options:
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
   cluster_template_id:
     description:
        - The template ID of cluster template.
     required: true
   discovery_url:
       description:
         - Url used for cluster node discovery
   docker_volume_size:
      description:
         - The size in GB of the docker volume
   flavor_id:
      description:
         - The flavor of the minion node for this ClusterTemplate
   keypair:
      description:
         - Name of the keypair to use.
   labels:
      description:
         - One or more key/value pairs
   master_flavor_id:
      description:
         - The flavor of the master node for this ClusterTemplate
   master_count:
      description:
         - The number of master nodes for this cluster
      default: 1
   name:
      description:
         - Name that has to be given to the cluster template
      required: true
   node_count:
      description:
         - The number of nodes for this cluster
      default: 1
   state:
      description:
         - Indicate desired state of the resource.
      choices: [present, absent]
      default: present
   timeout:
      description:
         - Timeout for creating the cluster in minutes. Default to 60 mins
           if not set
      default: 60
requirements: ["openstacksdk"]
'''

RETURN = '''
id:
    description: The cluster UUID.
    returned: On success when I(state) is 'present'
    type: str
    sample: "39007a7e-ee4f-4d13-8283-b4da2e037c69"
cluster:
    description: Dictionary describing the cluster.
    returned: On success when I(state) is 'present'
    type: complex
    contains:
      api_address:
          description:
            - Api address of cluster master node
          type: string
          sample: https://172.24.4.30:6443
      cluster_template_id:
          description: The cluster_template UUID
          type: string
          sample: '7b1418c8-cea8-48fc-995d-52b66af9a9aa'
      coe_version:
          description:
            - Version of the COE software currently running in this cluster
          type: string
          sample: v1.11.1
      container_version:
          description:
            - Version of the container software. Example: docker version.
          type: string
          sample: 1.12.6
      created_at:
          description:
            - The time in UTC at which the cluster is created
          type: datetime
          sample: 2018-08-16T10:29:45+00:00
      create_timeout:
          description:
            - Timeout for creating the cluster in minutes. Default to 60 if
              not set.
          type: int
          sample: 60
      discovery_url:
          description:
            - Url used for cluster node discovery
          type: string
          sample: https://discovery.etcd.io/a42ee38e7113f31f4d6324f24367aae5
      faults:
          description:
            - Fault info collected from the Heat resources of this cluster
          type: dict
          sample: {'0': 'ResourceInError: resources[0].resources...'}
      flavor_id:
          description:
            - The flavor of the minion node for this cluster
          type: string
          sample: c1.c1r1
      keypair:
          description:
            - Name of the keypair to use.
          type: string
          sample: mykey
      labels:
          description: One or more key/value pairs
          type: dict
          sample: {'key1': 'value1', 'key2': 'value2'}
      master_addresses:
          description:
            - IP addresses of cluster master nodes
          type: list
          sample: ['172.24.4.5']
      master_count:
          description:
            - The number of master nodes for this cluster.
          type: int
          sample: 1
      master_flavor_id:
          description:
            - The flavor of the master node for this cluster
          type: string
          sample: c1.c1r1
      name:
          description:
            - Name that has to be given to the cluster
          type: string
          sample: k8scluster
      node_addresses:
          description:
            - IP addresses of cluster slave nodes
          type: list
          sample: ['172.24.4.8']
      node_count:
          description:
            - The number of master nodes for this cluster.
          type: int
          sample: 1
      stack_id:
          description:
            - Stack id of the Heat stack
          type: string
          sample: '07767ec6-85f5-44cb-bd63-242a8e7f0d9d'
      status:
          description: Status of the cluster from the heat stack
          type: string
          sample: 'CREATE_COMLETE'
      status_reason:
          description:
            - Status reason of the cluster from the heat stack
          type: string
          sample: 'Stack CREATE completed successfully'
      updated_at:
          description:
            - The time in UTC at which the cluster is updated
          type: datetime
          sample: '2018-08-16T10:39:25+00:00'
      uuid:
          description:
            - Unique UUID for this cluster
          type: string
          sample: '86246a4d-a16c-4a58-9e96ad7719fe0f9d'
'''

EXAMPLES = '''
# Create a new Kubernetes cluster
- os_coe_cluster:
    name: k8s
    cluster_template_id: k8s-ha
    keypair: mykey
    master_count: 3
    node_count: 5
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def _parse_labels(labels):
    if isinstance(labels, str):
        labels_dict = {}
        for kv_str in labels.split(","):
            k, v = kv_str.split("=")
            labels_dict[k] = v
        return labels_dict
    if not labels:
        return {}
    return labels


def main():
    argument_spec = openstack_full_argument_spec(
        cluster_template_id=dict(required=True),
        discovery_url=dict(default=None),
        docker_volume_size=dict(type='int'),
        flavor_id=dict(default=None),
        keypair=dict(default=None),
        labels=dict(default=None, type='raw'),
        master_count=dict(type='int', default=1),
        master_flavor_id=dict(default=None),
        name=dict(required=True),
        node_count=dict(type='int', default=1),
        state=dict(default='present', choices=['absent', 'present']),
        timeout=dict(type='int', default=60),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    params = module.params.copy()

    state = module.params['state']
    name = module.params['name']
    cluster_template_id = module.params['cluster_template_id']

    kwargs = dict(
        discovery_url=module.params['discovery_url'],
        docker_volume_size=module.params['docker_volume_size'],
        flavor_id=module.params['flavor_id'],
        keypair=module.params['keypair'],
        labels=_parse_labels(params['labels']),
        master_count=module.params['master_count'],
        master_flavor_id=module.params['master_flavor_id'],
        node_count=module.params['node_count'],
        create_timeout=module.params['timeout'],
    )

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        changed = False
        cluster = cloud.get_coe_cluster(name_or_id=name, filters={'cluster_template_id': cluster_template_id})

        if state == 'present':
            if not cluster:
                cluster = cloud.create_coe_cluster(name, cluster_template_id=cluster_template_id, **kwargs)
                changed = True
            else:
                changed = False

            module.exit_json(changed=changed, cluster=cluster, id=cluster['uuid'])
        elif state == 'absent':
            if not cluster:
                module.exit_json(changed=False)
            else:
                cloud.delete_coe_cluster(name)
                module.exit_json(changed=True)
    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


if __name__ == "__main__":
    main()
