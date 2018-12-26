#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, Yannig Perré <yannig.perre@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# pylint: disable=invalid-name,dangerous-default-value,duplicate-code

"""Handle kops cluster creation/deletion"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.kops import Kops, to_camel_case

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: kops_cluster
short_description: Handle cluster creation with kops
description:
     - Let you create or delete cluster using kops
version_added: "2.8"
options:
  name:
     description:
       - FQDN name of the cluster (eg: test.example.org)
     type: string
     required: true
  state_store:
     description:
       - State store (eg: s3://my-state-store)
     type: string
     required: false
     default: None
  kops_cmd:
     description:
       - kops bin path
     type: string
     required: false
     default: None
  state:
     description:
       - If C(present), cluster will be created
       - If C(updated), cluster will be created and check that the cluster is updated
       - If C(absent), cluster will be deleted
     type: string
     required: false
     default: present
     choices: [ present, updated, absent ]
  additional_policies:
     description:
       - Additional policies for nodes in kops cluster
     type: dict
     required: false
     default: None
  docker:
     description:
       - Docker configuration
     type: dict
     required: false
     default: None
  admin_access:
     description:
       - Restrict API access to this CIDR.  If not set, access will not be restricted by IP.
     type: list
     required: false
     default: '[0.0.0.0/0]'
  api_loadbalancer_type:
     description:
       - Sets the API loadbalancer type to either 'public' or 'internal'
     type: string
     required: false
     default: None
  api_ssl_certificate:
     description:
       - Currently only supported in AWS. Sets the ARN of the SSL Certificate to use for the API server loadbalancer.
     type: string
     required: false
     default: None
  associate_public_ip:
     description:
       - Specify associate-public-ip=[true|false] to enable/disable association of public IP for master ASG and nodes. Default is 'true'.
     type: bool
     required: false
     default: None
  authorization:
     description:
       - Authorization mode to use: AlwaysAllow or RBAC
     type: string
     required: false
     default: 'RBAC'
  bastion:
     description:
       - Pass the bastion flag to enable a bastion instance group. Only applies to private topology.
     type: bool
     required: false
     default: None
  channel:
     description:
       - Channel for default versions and configuration to use
     type: string
     required: false
     default: 'stable'
  cloud:
     description:
       - Cloud provider to use - gce, aws, vsphere
     type: string
     required: false
     default: None
  cloud_labels:
     description:
       - A list of KV pairs used to tag all instance groups in AWS (eg "Owner=John Doe,Team=Some Team").
     type: string
     required: false
     default: None
  disable_subnet_tags:
     description:
       - Set to disable automatic subnet tagging
     type: bool
     required: false
     default: None
  dns:
     description:
       - DNS hosted zone to use: public|private.
     type: string
     required: false
     default: 'Public'
  dns_zone:
     description:
       - DNS hosted zone to use (defaults to longest matching zone)
     type: string
     required: false
     default: None
  dry_run:
     description:
       - If true, only print the object that would be sent, without sending it. This flag can be used to create a cluster YAML or JSON manifest.
     type: bool
     required: false
     default: None
  encrypt_etcd_storage:
     description:
       - Generate key in aws kms and use it for encrypt etcd volumes
     type: bool
     required: false
     default: None
  image:
     description:
       - Image to use for all instances.
     type: string
     required: false
     default: None
  kubernetes_version:
     description:
       - Version of kubernetes to run (defaults to version in channel)
     type: string
     required: false
     default: None
  master_count:
     description:
       - Set the number of masters.  Defaults to one master per master-zone
     type: int
     required: false
     default: None
  master_public_name:
     description:
       - Sets the public master public name
     type: string
     required: false
     default: None
  master_security_groups:
     description:
       - Add precreated additional security groups to masters.
     type: list
     required: false
     default: None
  master_size:
     description:
       - Set instance size for masters
     type: string
     required: false
     default: None
  master_tenancy:
     description:
       - The tenancy of the master group on AWS. Can either be default or dedicated.
     type: string
     required: false
     default: None
  master_volume_size:
     description:
       - Set instance volume size (in GB) for masters
     type: int
     required: false
     default: None
  master_zones:
     description:
       - Zones in which to run masters (must be an odd number)
     type: list
     required: false
     default: None
  model:
     description:
       - Models to apply (separate multiple models with commas)
     type: string
     required: false
     default: 'proto,cloudup'
  network_cidr:
     description:
       - Set to override the default network CIDR
     type: string
     required: false
     default: None
  networking:
     description:
       - Networking mode to use.  kubenet (default), classic, external, kopeio-vxlan (or kopeio), weave, flannel-vxlan (or flannel), flannel-udp, calico, canal, kube-router, romana, amazon-vpc-routed-eni, cilium.
     type: string
     required: false
     default: 'kubenet'
  node_count:
     description:
       - Set the number of nodes
     type: int
     required: false
     default: None
  node_security_groups:
     description:
       - Add precreated additional security groups to nodes.
     type: list
     required: false
     default: None
  node_size:
     description:
       - Set instance size for nodes
     type: string
     required: false
     default: None
  node_tenancy:
     description:
       - The tenancy of the node group on AWS. Can be either default or dedicated.
     type: string
     required: false
     default: None
  node_volume_size:
     description:
       - Set instance volume size (in GB) for nodes
     type: int
     required: false
     default: None
  out:
     description:
       - Path to write any local output
     type: string
     required: false
     default: None
  project:
     description:
       - Project to use (must be set on GCE)
     type: string
     required: false
     default: None
  ssh_access:
     description:
       - Restrict SSH access to this CIDR.  If not set, access will not be restricted by IP.
     type: list
     required: false
     default: '[0.0.0.0/0]'
  ssh_public_key:
     description:
       - SSH public key to use (defaults to ~/.ssh/id_rsa.pub on AWS)
     type: string
     required: false
     default: None
  subnets:
     description:
       - Set to use shared subnets
     type: list
     required: false
     default: None
  target:
     description:
       - Valid targets: direct, terraform, cloudformation. Set this flag to terraform if you want kops to generate terraform
     type: string
     required: false
     default: 'direct'
  topology:
     description:
       - Controls network topology for the cluster: public|private.
     type: string
     required: false
     default: 'public'
  utility_subnets:
     description:
       - Set to use shared utility subnets
     type: list
     required: false
     default: None
  vpc:
     description:
       - Set to use a shared VPC
     type: string
     required: false
     default: None
  zones:
     description:
       - Zones in which to run the cluster
     type: list
     required: false
     default: None
  bastion_interval:
     description:
       - Time to wait between restarting bastions
     type: string
     required: false
     default: '5m0s'
  cloudonly:
     description:
       - Perform rolling update without confirming progress with k8s
     type: bool
     required: false
     default: None
  fail_on_drain_error:
     description:
       - The rolling-update will fail if draining a node fails.
     type: bool
     required: false
     default: 'true'
  fail_on_validate_error:
     description:
       - The rolling-update will fail if the cluster fails to validate.
     type: bool
     required: false
     default: 'true'
  force:
     description:
       - Force rolling update, even if no changes
     type: bool
     required: false
     default: None
  instance_group:
     description:
       - List of instance groups to update (defaults to all if not specified)
     type: list
     required: false
     default: None
  instance_group_roles:
     description:
       - If specified, only instance groups of the specified role will be updated (e.g. Master,Node,Bastion)
     type: list
     required: false
     default: None
  master_interval:
     description:
       - Time to wait between restarting masters
     type: string
     required: false
     default: '5m0s'
  node_interval:
     description:
       - Time to wait between restarting nodes
     type: string
     required: false
     default: '4m0s'
notes:
   - kops bin is required
author:
   - Yannig Perré
'''

EXAMPLES = '''
- name: Create kube cluster with kops
  kops_cluster:
    name: test
    state: present
'''

RETURN = '''
---
'''

class KopsCluster(Kops):
    """Handle state for kops cluster"""

    SPECIAL_CASE = {
        "admin_access": {
            "field": "kubernetesApiAccess",
            "transform": "list"
        },
        "ssh_access": {
            "transform": "list"
        }
    }

    def __init__(self):
        """Init module parameters"""
        additional_module_args = dict(
            state=dict(choices=['present', 'absent', 'updated'], default='present'),
            cloud=dict(choices=['gce', 'aws', 'vsphere'], default='aws'),
            docker=dict(type=dict),
            additional_policies=dict(type=dict, aliases=['additional-policies', 'additionalPolicies']),
            admin_access=dict(type=str, aliases=['admin-access']),
            api_loadbalancer_type=dict(type=str, aliases=['api-loadbalancer-type']),
            api_ssl_certificate=dict(type=str, aliases=['api-ssl-certificate']),
            associate_public_ip=dict(type=bool, aliases=['associate-public-ip']),
            authorization=dict(type=str),
            bastion=dict(type=bool),
            channel=dict(type=str),

            cloud_labels=dict(type=str, aliases=['cloud-labels']),
            disable_subnet_tags=dict(type=bool, aliases=['disable-subnet-tags']),
            dns=dict(type=str),
            dns_zone=dict(type=str, aliases=['dns-zone']),
            dry_run=dict(type=bool, aliases=['dry-run']),
            encrypt_etcd_storage=dict(type=bool, aliases=['encrypt-etcd-storage']),
            image=dict(type=str),
            kubernetes_version=dict(type=str, aliases=['kubernetes-version']),
            master_count=dict(type=int, aliases=['master-count']),
            master_public_name=dict(type=str, aliases=['master-public-name']),
            master_security_groups=dict(type=str, aliases=['master-security-groups']),
            master_size=dict(type=str, aliases=['master-size']),
            master_tenancy=dict(type=str, aliases=['master-tenancy']),
            master_volume_size=dict(type=int, aliases=['master-volume-size']),
            master_zones=dict(type=str, aliases=['master-zones']),
            model=dict(type=str),
            network_cidr=dict(type=str, aliases=['network-cidr']),
            networking=dict(type=str),
            node_count=dict(type=int, aliases=['node-count']),
            node_security_groups=dict(type=str, aliases=['node-security-groups']),
            node_size=dict(type=str, aliases=['node-size']),
            node_tenancy=dict(type=str, aliases=['node-tenancy']),
            node_volume_size=dict(type=int, aliases=['node-volume-size']),
            out=dict(type=str),
            project=dict(type=str),
            ssh_access=dict(type=str, aliases=['ssh-access']),
            ssh_public_key=dict(type=str, aliases=['ssh-public-key']),
            subnets=dict(type=str),
            target=dict(type=str),
            topology=dict(type=str),
            utility_subnets=dict(type=str, aliases=['utility-subnets']),
            vpc=dict(type=str),
            zones=dict(type=str),
            bastion_interval=dict(type=str, aliases=['bastion-interval']),
            cloudonly=dict(type=bool),
            fail_on_drain_error=dict(type=bool, aliases=['fail-on-drain-error']),
            fail_on_validate_error=dict(type=bool, aliases=['fail-on-validate-error']),
            force=dict(type=bool),
            instance_group=dict(type=str, aliases=['instance-group']),
            instance_group_roles=dict(type=str, aliases=['instance-group-roles']),
            master_interval=dict(type=str, aliases=['master-interval']),
            node_interval=dict(type=str, aliases=['node-interval']),
        )
        # pylint: disable=line-too-long
        options_definition = {
            'admin_access': {'name': 'admin_access', 'alias': 'admin-access', 'type': 'list', 'help': 'Restrict API access to this CIDR.  If not set, access will not be restricted by IP.', 'default': "'[0.0.0.0/0]'", 'tag': 'create'},
            'api_loadbalancer_type': {'name': 'api_loadbalancer_type', 'alias': 'api-loadbalancer-type', 'type': 'str', 'help': "Sets the API loadbalancer type to either 'public' or 'internal'", 'default': None, 'tag': 'create'},
            'api_ssl_certificate': {'name': 'api_ssl_certificate', 'alias': 'api-ssl-certificate', 'type': 'str', 'help': 'Currently only supported in AWS. Sets the ARN of the SSL Certificate to use for the API server loadbalancer.', 'default': None, 'tag': 'create'},
            'associate_public_ip': {'name': 'associate_public_ip', 'alias': 'associate-public-ip', 'type': 'bool', 'help': "Specify --associate-public-ip=[true|false] to enable/disable association of public IP for master ASG and nodes. Default is 'true'.", 'default': None, 'tag': 'create'},
            'authorization': {'name': 'authorization', 'alias': 'authorization', 'type': 'str', 'help': 'Authorization mode to use: AlwaysAllow or RBAC', 'default': "'RBAC'", 'tag': 'create'},
            'bastion': {'name': 'bastion', 'alias': 'bastion', 'type': 'bool', 'help': 'Pass the --bastion flag to enable a bastion instance group. Only applies to private topology.', 'default': None, 'tag': 'create'},
            'channel': {'name': 'channel', 'alias': 'channel', 'type': 'str', 'help': 'Channel for default versions and configuration to use', 'default': "'stable'", 'tag': 'create'},
            'cloud': {'name': 'cloud', 'alias': 'cloud', 'type': 'str', 'help': 'Cloud provider to use - gce, aws, vsphere', 'default': None, 'tag': 'create'},
            'cloud_labels': {'name': 'cloud_labels', 'alias': 'cloud-labels', 'type': 'str', 'help': 'A list of KV pairs used to tag all instance groups in AWS (eg "Owner=John Doe,Team=Some Team").', 'default': None, 'tag': 'create'},
            'disable_subnet_tags': {'name': 'disable_subnet_tags', 'alias': 'disable-subnet-tags', 'type': 'bool', 'help': 'Set to disable automatic subnet tagging', 'default': None, 'tag': 'create'},
            'dns': {'name': 'dns', 'alias': 'dns', 'type': 'str', 'help': 'DNS hosted zone to use: public|private.', 'default': "'Public'", 'tag': 'create'},
            'dns_zone': {'name': 'dns_zone', 'alias': 'dns-zone', 'type': 'str', 'help': 'DNS hosted zone to use (defaults to longest matching zone)', 'default': None, 'tag': 'create'},
            'dry_run': {'name': 'dry_run', 'alias': 'dry-run', 'type': 'bool', 'help': 'If true, only print the object that would be sent, without sending it. This flag can be used to create a cluster YAML or JSON manifest.', 'default': None, 'tag': 'create'},
            'encrypt_etcd_storage': {'name': 'encrypt_etcd_storage', 'alias': 'encrypt-etcd-storage', 'type': 'bool', 'help': 'Generate key in aws kms and use it for encrypt etcd volumes', 'default': None, 'tag': 'create'},
            'image': {'name': 'image', 'alias': 'image', 'type': 'str', 'help': 'Image to use for all instances.', 'default': None, 'tag': 'create'},
            'kubernetes_version': {'name': 'kubernetes_version', 'alias': 'kubernetes-version', 'type': 'str', 'help': 'Version of kubernetes to run (defaults to version in channel)', 'default': None, 'tag': 'create'},
            'master_count': {'name': 'master_count', 'alias': 'master-count', 'type': 'int', 'help': 'Set the number of masters.  Defaults to one master per master-zone', 'default': None, 'tag': 'create'},
            'master_public_name': {'name': 'master_public_name', 'alias': 'master-public-name', 'type': 'str', 'help': 'Sets the public master public name', 'default': None, 'tag': 'create'},
            'master_security_groups': {'name': 'master_security_groups', 'alias': 'master-security-groups', 'type': 'list', 'help': 'Add precreated additional security groups to masters.', 'default': None, 'tag': 'create'},
            'master_size': {'name': 'master_size', 'alias': 'master-size', 'type': 'str', 'help': 'Set instance size for masters', 'default': None, 'tag': 'create'},
            'master_tenancy': {'name': 'master_tenancy', 'alias': 'master-tenancy', 'type': 'str', 'help': 'The tenancy of the master group on AWS. Can either be default or dedicated.', 'default': None, 'tag': 'create'},
            'master_volume_size': {'name': 'master_volume_size', 'alias': 'master-volume-size', 'type': 'int', 'help': 'Set instance volume size (in GB) for masters', 'default': None, 'tag': 'create'},
            'master_zones': {'name': 'master_zones', 'alias': 'master-zones', 'type': 'list', 'help': 'Zones in which to run masters (must be an odd number)', 'default': None, 'tag': 'create'},
            'model': {'name': 'model', 'alias': 'model', 'type': 'str', 'help': 'Models to apply (separate multiple models with commas)', 'default': "'proto,cloudup'", 'tag': 'create'},
            'network_cidr': {'name': 'network_cidr', 'alias': 'network-cidr', 'type': 'str', 'help': 'Set to override the default network CIDR', 'default': None, 'tag': 'create'},
            'networking': {'name': 'networking', 'alias': 'networking', 'type': 'str', 'help': 'Networking mode to use.  kubenet (default), classic, external, kopeio-vxlan (or kopeio), weave, flannel-vxlan (or flannel), flannel-udp, calico, canal, kube-router, romana, amazon-vpc-routed-eni, cilium.', 'default': "'kubenet'", 'tag': 'create'},
            'node_count': {'name': 'node_count', 'alias': 'node-count', 'type': 'int', 'help': 'Set the number of nodes', 'default': None, 'tag': 'create'},
            'node_security_groups': {'name': 'node_security_groups', 'alias': 'node-security-groups', 'type': 'list', 'help': 'Add precreated additional security groups to nodes.', 'default': None, 'tag': 'create'},
            'node_size': {'name': 'node_size', 'alias': 'node-size', 'type': 'str', 'help': 'Set instance size for nodes', 'default': None, 'tag': 'create'},
            'node_tenancy': {'name': 'node_tenancy', 'alias': 'node-tenancy', 'type': 'str', 'help': 'The tenancy of the node group on AWS. Can be either default or dedicated.', 'default': None, 'tag': 'create'},
            'node_volume_size': {'name': 'node_volume_size', 'alias': 'node-volume-size', 'type': 'int', 'help': 'Set instance volume size (in GB) for nodes', 'default': None, 'tag': 'create'},
            'out': {'name': 'out', 'alias': 'out', 'type': 'str', 'help': 'Path to write any local output', 'default': None, 'tag': 'create'},
            'project': {'name': 'project', 'alias': 'project', 'type': 'str', 'help': 'Project to use (must be set on GCE)', 'default': None, 'tag': 'create'},
            'ssh_access': {'name': 'ssh_access', 'alias': 'ssh-access', 'type': 'list', 'help': 'Restrict SSH access to this CIDR.  If not set, access will not be restricted by IP.', 'default': "'[0.0.0.0/0]'", 'tag': 'create'},
            'ssh_public_key': {'name': 'ssh_public_key', 'alias': 'ssh-public-key', 'type': 'str', 'help': 'SSH public key to use (defaults to ~/.ssh/id_rsa.pub on AWS)', 'default': None, 'tag': 'create'},
            'subnets': {'name': 'subnets', 'alias': 'subnets', 'type': 'list', 'help': 'Set to use shared subnets', 'default': None, 'tag': 'create'},
            'target': {'name': 'target', 'alias': 'target', 'type': 'str', 'help': 'Valid targets: direct, terraform, cloudformation. Set this flag to terraform if you want kops to generate terraform', 'default': "'direct'", 'tag': 'create'},
            'topology': {'name': 'topology', 'alias': 'topology', 'type': 'str', 'help': 'Controls network topology for the cluster: public|private.', 'default': "'public'", 'tag': 'create'},
            'utility_subnets': {'name': 'utility_subnets', 'alias': 'utility-subnets', 'type': 'list', 'help': 'Set to use shared utility subnets', 'default': None, 'tag': 'create'},
            'vpc': {'name': 'vpc', 'alias': 'vpc', 'type': 'str', 'help': 'Set to use a shared VPC', 'default': None, 'tag': 'create'},
            'zones': {'name': 'zones', 'alias': 'zones', 'type': 'list', 'help': 'Zones in which to run the cluster', 'default': None, 'tag': 'create'},
            'bastion_interval': {'name': 'bastion_interval', 'alias': 'bastion-interval', 'type': 'str', 'help': 'Time to wait between restarting bastions', 'default': "'5m0s'", 'tag': 'rolling-update'},
            'cloudonly': {'name': 'cloudonly', 'alias': 'cloudonly', 'type': 'bool', 'help': 'Perform rolling update without confirming progress with k8s', 'default': None, 'tag': 'rolling-update'},
            'fail_on_drain_error': {'name': 'fail_on_drain_error', 'alias': 'fail-on-drain-error', 'type': 'bool', 'help': 'The rolling-update will fail if draining a node fails.', 'default': "'true'", 'tag': 'rolling-update'},
            'fail_on_validate_error': {'name': 'fail_on_validate_error', 'alias': 'fail-on-validate-error', 'type': 'bool', 'help': 'The rolling-update will fail if the cluster fails to validate.', 'default': "'true'", 'tag': 'rolling-update'},
            'force': {'name': 'force', 'alias': 'force', 'type': 'bool', 'help': 'Force rolling update, even if no changes', 'default': None, 'tag': 'rolling-update'},
            'instance_group': {'name': 'instance_group', 'alias': 'instance-group', 'type': 'list', 'help': 'List of instance groups to update (defaults to all if not specified)', 'default': None, 'tag': 'rolling-update'},
            'instance_group_roles': {'name': 'instance_group_roles', 'alias': 'instance-group-roles', 'type': 'list', 'help': 'If specified, only instance groups of the specified role will be updated (e.g. Master,Node,Bastion)', 'default': None, 'tag': 'rolling-update'},
            'master_interval': {'name': 'master_interval', 'alias': 'master-interval', 'type': 'str', 'help': 'Time to wait between restarting masters', 'default': "'5m0s'", 'tag': 'rolling-update'},
            'node_interval': {'name': 'node_interval', 'alias': 'node-interval', 'type': 'str', 'help': 'Time to wait between restarting nodes', 'default': "'4m0s'", 'tag': 'rolling-update'},
        }
        super(KopsCluster, self).__init__(additional_module_args, options_definition)


    def delete_cluster(self, cluster_name):
        """Delete cluster"""
        (result, out, err) = self.run_command(
            ["delete", "cluster", "--yes", "--name", cluster_name]
        )
        if result > 0:
            self.module.fail_json(msg=err)
        return dict(
            changed=True,
            kops_output=out,
            cluster_name=cluster_name,
        )


    def create_cluster(self, cluster_name):
        """Create cluster using kops"""
        cmd = ["create", "cluster", "--name", cluster_name]

        if self.module.params['state'] in ['updated', 'started']:
            cmd.append("--yes")

        (result, out, err) = self.run_command(cmd, add_optional_args_from_tag="create")
        if result > 0:
            self.module.fail_json(msg=err)

        # Handle docker definition (version, options)
        self.update_cluster(cluster_name)

        return dict(
            changed=True,
            cluster_name=cluster_name,
            kops_output=out
        )


    def get_spec_name(self, param):
        """
          Send back variable name as expected in spec field from param name
          Handle corner case like Cidr/CIDR or special case
        """
        if param in self.SPECIAL_CASE and self.SPECIAL_CASE[param].get('field'):
            return self.SPECIAL_CASE[param]['field']

        return to_camel_case(param).replace('Cidr', 'CIDR')

    def convert_value(self, param, value):
        """Do some transformation from string to list using SPECIAL_CASE values"""
        if param in self.SPECIAL_CASE:
            if self.SPECIAL_CASE[param]['transform'] == 'list':
                return [x.strip() for x in value.split(",")]
        # If not a special case, send unchanged value
        return value

    def update_cluster(self, cluster_name):
        """Update cluster"""
        cluster_definition = self.get_clusters(cluster_name)

        spec_to_merge = {}
        cluster_parameters = [
            'kubernetes_version', 'master_public_name', 'network_cidr',
            'admin_access', 'ssh_access', 'docker', 'additional_policies',
        ]
        for param in cluster_parameters:
            spec_name = self.get_spec_name(param)
            value = self.module.params[param]
            if spec_name in cluster_definition['spec']:
                current_value = cluster_definition['spec'][spec_name]
            else:
                current_value = None

            if value is not None and value != current_value:
                spec_to_merge[spec_name] = value

        return self.update_object_definition(cluster_name, cluster_definition, spec_to_merge)


    def apply_present(self, cluster_name, defined_cluster):
        """Create cluster if does not exist"""
        if defined_cluster:
            changed = self.update_cluster(cluster_name)
            if self.module.params['state'] in ['updated', 'started']:
                return self._apply_modifications(cluster_name)
            if changed:
                defined_cluster = self.get_clusters(cluster_name)
            return dict(
                changed=changed,
                cluster_name=cluster_name,
                defined_cluster=defined_cluster
            )
        return self.create_cluster(cluster_name)


    def apply_absent(self, cluster_name, cluster_exist):
        """Delete cluster if cluster exist"""
        if not cluster_exist:
            return dict(
                changed=False,
                cluster_name=cluster_name,
            )
        return self.delete_cluster(cluster_name)


    def check_cluster_state(self):
        """Check cluster state and apply expected state"""
        cluster_name = self.module.params['name']
        state = self.module.params['state']
        defined_cluster = self.get_clusters(
            cluster_name=cluster_name,
            retrieve_ig=False,
            failed_when_not_found=False
        )

        if state in ['present', 'updated']:
            return self.apply_present(cluster_name, defined_cluster)

        if state == 'absent':
            return self.apply_absent(cluster_name, defined_cluster)

        self.module.fail_json(msg="Operation not supported", defined_cluster=defined_cluster)
        return None


    def exit_json(self):
        """Send back result to Ansible"""
        results = self.check_cluster_state()

        self.module.exit_json(**results)


def main():
    """Kops cluster handling"""
    cluster = KopsCluster()
    cluster.exit_json()


if __name__ == '__main__':
    main()
