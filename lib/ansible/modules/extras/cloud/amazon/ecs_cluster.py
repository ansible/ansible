#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: ecs_cluster
short_description: create or terminate ecs clusters
notes:
    - When deleting a cluster, the information returned is the state of the cluster prior to deletion.
    - It will also wait for a cluster to have instances registered to it.
description:
    - Creates or terminates ecs clusters.
version_added: "1.9"
requirements: [ json, time, boto, boto3 ]
options:
        state=dict(required=True, choices=['present', 'absent', 'has_instances'] ),
        name=dict(required=True, type='str' ),
        delay=dict(required=False, type='int', default=10),
        repeat=dict(required=False, type='int', default=10)

    state:
        description:
            - The desired state of the cluster
        required: true
        choices: ['present', 'absent', 'has_instances']
    name:
        description:
            - The cluster name
        required: true
    delay:
        description:
            - Number of seconds to wait
        required: true
    name:
        description:
            - The cluster name
        required: true
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Cluster creation
- ecs_cluster:
    name: default
    state: present

# Cluster deletion
- ecs_cluster:
    name: default
    state: absent

- name: Wait for register
  ecs_cluster:
    name: "{{ new_cluster }}"
    state: has_instances
    delay: 10
    repeat: 10
  register: task_output

'''
RETURN = '''
activeServicesCount:
    description: how many services are active in this cluster
    returned: 0 if a new cluster
    type: int
clusterArn:
    description: the ARN of the cluster just created
    type: string (ARN)
    sample: arn:aws:ecs:us-west-2:172139249013:cluster/test-cluster-mfshcdok
clusterName:
    description: name of the cluster just created (should match the input argument)
    type: string
    sample: test-cluster-mfshcdok
pendingTasksCount:
    description: how many tasks are waiting to run in this cluster
    returned: 0 if a new cluster
    type: int
registeredContainerInstancesCount:
    description: how many container instances are available in this cluster
    returned: 0 if a new cluster
    type: int
runningTasksCount:
    description: how many tasks are running in this cluster
    returned: 0 if a new cluster
    type: int
status:
    description: the status of the new cluster
    returned: ACTIVE
    type: string
'''
try:
    import json, time
    import boto
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

class EcsClusterManager:
    """Handles ECS Clusters"""

    def __init__(self, module):
        self.module = module

        try:
            # self.ecs = boto3.client('ecs')
            region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
            if not region:
                module.fail_json(msg="Region must be specified as a parameter, in EC2_REGION or AWS_REGION environment variables or in boto configuration file")
            self.ecs = boto3_conn(module, conn_type='client', resource='ecs', region=region, endpoint=ec2_url, **aws_connect_kwargs)
        except boto.exception.NoAuthHandlerFound, e:
            self.module.fail_json(msg=str(e))

    def find_in_array(self, array_of_clusters, cluster_name, field_name='clusterArn'):
        for c in array_of_clusters:
            if c[field_name].endswith(cluster_name):
                return c
        return None

    def describe_cluster(self, cluster_name):
        response = self.ecs.describe_clusters(clusters=[
            cluster_name
        ])
        if len(response['failures'])>0:
            c = self.find_in_array(response['failures'], cluster_name, 'arn')
            if c and c['reason']=='MISSING':
                return None
            # fall thru and look through found ones
        if len(response['clusters'])>0:
            c = self.find_in_array(response['clusters'], cluster_name)
            if c:
                return c
        raise StandardError("Unknown problem describing cluster %s." % cluster_name)

    def create_cluster(self, clusterName = 'default'):
        response = self.ecs.create_cluster(clusterName=clusterName)
        return response['cluster']

    def delete_cluster(self, clusterName):
        return self.ecs.delete_cluster(cluster=clusterName)

def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(required=True, choices=['present', 'absent', 'has_instances'] ),
        name=dict(required=True, type='str' ),
        delay=dict(required=False, type='int', default=10),
        repeat=dict(required=False, type='int', default=10)
    ))
    required_together = ( ['state', 'name'] )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True, required_together=required_together)

    if not HAS_BOTO:
      module.fail_json(msg='boto is required.')

    if not HAS_BOTO3:
      module.fail_json(msg='boto3 is required.')

    cluster_name = module.params['name']

    cluster_mgr = EcsClusterManager(module)
    try:
        existing = cluster_mgr.describe_cluster(module.params['name'])
    except Exception, e:
        module.fail_json(msg=str(e))

    results = dict(changed=False)
    if module.params['state'] == 'present':
        if existing and 'status' in existing and existing['status']=="ACTIVE":
            results['cluster']=existing
        else:
            if not module.check_mode:
                # doesn't exist. create it.
                results['cluster'] = cluster_mgr.create_cluster(module.params['name'])
            results['changed'] = True

    # delete the cluster
    elif module.params['state'] == 'absent':
        if not existing:
            pass
        else:
            # it exists, so we should delete it and mark changed.
            # return info about the cluster deleted
            results['cluster'] = existing
            if 'status' in existing and existing['status']=="INACTIVE":
                results['changed'] = False
            else:
                if not module.check_mode:
                    cluster_mgr.delete_cluster(module.params['name'])
                results['changed'] = True
    elif module.params['state'] == 'has_instances':
        if not existing:
            module.fail_json(msg="Cluster '"+module.params['name']+" not found.")
            return
        # it exists, so we should delete it and mark changed.
        # return info about the cluster deleted
        delay = module.params['delay']
        repeat = module.params['repeat']
        time.sleep(delay)
        count = 0
        for i in range(repeat):
            existing = cluster_mgr.describe_cluster(module.params['name'])
            count = existing['registeredContainerInstancesCount']
            if count > 0:
                results['changed'] = True
                break
            time.sleep(delay)
        if count == 0 and i is repeat-1:
            module.fail_json(msg="Cluster instance count still zero after "+str(repeat)+" tries of "+str(delay)+" seconds each.")
            return

    module.exit_json(**results)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
