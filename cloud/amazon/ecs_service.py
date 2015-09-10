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
module: ecs_service
short_description: create, terminate, start or stop a service in ecs
description:
    - Creates or terminates ec2 instances.
notes:
    - the service role specified must be assumable (i.e. have a trust relationship
    for the ecs service, ecs.amazonaws.com)
dependecies:
    - An IAM role must have been created
version_added: "2.0"
options:
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Basic provisioning example
- ecs_service:
    name: default
    state: present
    cluster: string
# Simple example to delete
- ecs_cluster:
    name: default
    state: absent
    cluster: string
'''
RETURN = '''
cache_updated:
    description: if the cache was updated or not
    returned: success, in some cases
    type: boolean
    sample: True
cache_update_time:
    description: time of the last cache update (0 if unknown)
    returned: success, in some cases
    type: datetime
    sample: 1425828348000
stdout:
    description: output from apt
    returned: success, when needed
    type: string
    sample: "Reading package lists...\nBuilding dependency tree...\nReading state information...\nThe following extra packages will be installed:\n  apache2-bin ..."
stderr:
    description: error output from apt
    returned: success, when needed
    type: string
    sample: "AH00558: apache2: Could not reliably determine the server's fully qualified domain name, using 127.0.1.1. Set the 'ServerName' directive globally to ..."
'''
try:
    import json
    import boto
    import botocore
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

class EcsServiceManager:
    """Handles ECS Services"""

    def __init__(self, module):
        self.module = module

        try:
            # self.ecs = boto3.client('ecs')
            region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
            if not region:
                module.fail_json(msg="Region must be specified as a parameter, in EC2_REGION or AWS_REGION environment variables or in boto configuration file")
            self.ecs = boto3_conn(module, conn_type='client', resource='ecs', region=region, endpoint=ec2_url, **aws_connect_kwargs)
        except boto.exception.NoAuthHandlerFound, e:
            self.module.fail_json(msg="Can't authorize connection - "+str(e))

    # def list_clusters(self):
    # 	return self.client.list_clusters()
    # {'failures=[],
    # 'ResponseMetadata={'HTTPStatusCode=200, 'RequestId='ce7b5880-1c41-11e5-8a31-47a93a8a98eb'},
    # 'clusters=[{'activeServicesCount=0, 'clusterArn='arn:aws:ecs:us-west-2:777110527155:cluster/default', 'status='ACTIVE', 'pendingTasksCount=0, 'runningTasksCount=0, 'registeredContainerInstancesCount=0, 'clusterName='default'}]}
    # {'failures=[{'arn='arn:aws:ecs:us-west-2:777110527155:cluster/bogus', 'reason='MISSING'}],
    # 'ResponseMetadata={'HTTPStatusCode=200, 'RequestId='0f66c219-1c42-11e5-8a31-47a93a8a98eb'},
    # 'clusters=[]}

    def find_in_array(self, array_of_services, service_name, field_name='serviceArn'):
        for c in array_of_services:
            if c[field_name].endswith(service_name):
                return c
        return None

    def describe_service(self, cluster_name, service_name):
        response = self.ecs.describe_services(
            cluster=cluster_name,
            services=[
                service_name
        ])
        msg = ''
        if len(response['failures'])>0:
            c = self.find_in_array(response['failures'], service_name, 'arn')
            msg += ", failure reason is "+c['reason']
            if c and c['reason']=='MISSING':
                return None
            # fall thru and look through found ones
        if len(response['services'])>0:
            c = self.find_in_array(response['services'], service_name)
            if c:
                return c
        raise StandardError("Unknown problem describing service %s." % service_name)

    def create_service(self, service_name, cluster_name, task_definition,
        load_balancers, desired_count, client_token, role):
        response = self.ecs.create_service(
            cluster=cluster_name,
            serviceName=service_name,
            taskDefinition=task_definition,
            loadBalancers=load_balancers,
            desiredCount=desired_count,
            clientToken=client_token,
            role=role)
        # some fields are datetime which is not JSON serializable
        # make them strings
        service = response['service']
        if 'deployments' in service:
            for d in service['deployments']:
                if 'createdAt' in d:
                    d['createdAt'] = str(d['createdAt'])
                if 'updatedAt' in d:
                    d['updatedAt'] = str(d['updatedAt'])
        if 'events' in service:
            for e in service['events']:
                if 'createdAt' in e:
                    e['createdAt'] = str(e['createdAt'])
        return service

    def delete_service(self, service, cluster=None):
        return self.ecs.delete_service(cluster=cluster, service=service)

def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(required=True, choices=['present', 'absent', 'deleting'] ),
        name=dict(required=True, type='str' ),
        cluster=dict(required=False, type='str' ),
        task_definition=dict(required=False, type='str' ),
        load_balancers=dict(required=False, type='list' ),
        desired_count=dict(required=False, type='int' ),
        client_token=dict(required=False, type='str' ),
        role=dict(required=False, type='str' ),
        delay=dict(required=False, type='int', default=10),
        repeat=dict(required=False, type='int', default=10)
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_BOTO:
      module.fail_json(msg='boto is required.')

    if not HAS_BOTO3:
      module.fail_json(msg='boto3 is required.')

    if module.params['state'] == 'present':
        if not 'task_definition' in module.params and module.params['task_definition'] is None:
            module.fail_json(msg="To use create a service, a task_definition must be specified")
        if not 'desired_count' in module.params and module.params['desired_count'] is None:
            module.fail_json(msg="To use create a service, a desired_count must be specified")

    service_mgr = EcsServiceManager(module)
    try:
        existing = service_mgr.describe_service(module.params['cluster'], module.params['name'])
    except Exception, e:
        module.fail_json(msg="Exception describing service '"+module.params['name']+"' in cluster '"+module.params['cluster']+"': "+str(e))

    results = dict(changed=False )
    if module.params['state'] == 'present':
        if existing and 'status' in existing and existing['status']=="ACTIVE":
            del existing['deployments']
            del existing['events']
            results['service']=existing
        else:
            if not module.check_mode:
                if module.params['load_balancers'] is None:
                    loadBalancers = []
                else:
                    loadBalancers = module.params['load_balancers']
                if module.params['role'] is None:
                    role = ''
                else:
                    role = module.params['role']
                if module.params['client_token'] is None:
                    clientToken = ''
                else:
                    clientToken = module.params['client_token']
                # doesn't exist. create it.
                response = service_mgr.create_service(module.params['name'],
                    module.params['cluster'],
                    module.params['task_definition'],
                    loadBalancers,
                    module.params['desired_count'],
                    clientToken,
                    role)
                # the bad news is the result has datetime fields that aren't JSON serializable
                # nuk'em!

                del response['deployments']
                del response['events']
                
                results['service'] = response

            results['changed'] = True

    elif module.params['state'] == 'absent':
        if not existing:
            pass
        else:
            # it exists, so we should delete it and mark changed.
            # return info about the cluster deleted
            del existing['deployments']
            del existing['events']
            results['ansible_facts'] = existing
            if 'status' in existing and existing['status']=="INACTIVE":
                results['changed'] = False
            else:
                if not module.check_mode:
                    try:
                        service_mgr.delete_service(
                            module.params['name'],
                            module.params['cluster']
                        )
                    except botocore.exceptions.ClientError, e:
                        module.fail_json(msg=e.message)
                results['changed'] = True

    elif module.params['state'] == 'deleting':
        if not existing:
            module.fail_json(msg="Service '"+module.params['name']+" not found.")
            return
        # it exists, so we should delete it and mark changed.
        # return info about the cluster deleted
        delay = module.params['delay']
        repeat = module.params['repeat']
        time.sleep(delay)
        for i in range(repeat):
            existing = service_mgr.describe_service(module.params['cluster'], module.params['name'])
            status = existing['status']
            if status == "INACTIVE":
                results['changed'] = True
                break
            time.sleep(delay)
        if i is repeat-1:
            module.fail_json(msg="Service still not deleted after "+str(repeat)+" tries of "+str(delay)+" seconds each.")
            return

    module.exit_json(**results)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
