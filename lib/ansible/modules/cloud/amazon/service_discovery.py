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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: service_discovery
short_description: thin wrap for boto3 servicediscovery client
description:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/servicediscovery.html
    service discovery comes in two parts, a namespace and a service discovery "registry"
    Namespace is somewhat owned by route53
    Registries are owned by the namespace
    ECS containers may announce themselves to the registry
    There may be other things that use registries
    This module tries to allow creating service discovery registries
notes:
    
version_added: "2.8"
author:
    - "tad merchant @ezmac"

requirements: [ json, botocore, boto3 ]
options:
    state:
        description:
          - The desired state of the service
        required: true
        choices: ["present", "absent"]
    name:
        description:
          - The name of the service
        required: true
    creator_request_id:
        description:
          - A unique string that identifies the request and that allows failed CreateService requests to be retried without the risk of executing the operation twice. CreatorRequestId can be any unique string, for example, a date/time stamp.
This field is autopopulated if not provided.
        required: false
    description:
        description: Description for the service.
    dns_config: 
        required: True
        description:
           Required even when deleting to get the namespace_id; At minimum, dns_config may have only the namespace_id when deleting
           for any creation, a full dns_config is required
           A complex type that contains information about the records that you want Route 53 to create when you register an instance.
           Something like: {
              namespace_id: string
              routing_policy: [MULTIVALUE, WEIGHTED]
              dns_records:[
                {
                  Type: [A, AAAA, SRV, CNAME],
                  TTL: int,
                  }]
              }
    health_check_config:
        required: false
        description: Public dns only
        {
          Type: "string" ([HTTP, HTTPS, TCP]),
          ResourcePath: "string",
          FailureThreshold: int
        }

    health_check_custom_config:
        required: False
        description: Private DNS only
        {
          failure_threshold: int
        }
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.
'''

RETURN = '''
Probably something like:
{
    'Service': {
        'Id': 'string',
        'Arn': 'string',
        'Name': 'string',
        'Description': 'string',
        'InstanceCount': 123,
        'DnsConfig': {
            'NamespaceId': 'string',
            'RoutingPolicy': 'MULTIVALUE'|'WEIGHTED',
            'DnsRecords': [
                {
                    'Type': 'SRV'|'A'|'AAAA'|'CNAME',
                    'TTL': 123
                },
            ]
        },
        'HealthCheckConfig': {
            'Type': 'HTTP'|'HTTPS'|'TCP',
            'ResourcePath': 'string',
            'FailureThreshold': 123
        },
        'HealthCheckCustomConfig': {
            'FailureThreshold': 123
        },
        'CreateDate': datetime(2015, 1, 1),
        'CreatorRequestId': 'string'
    }
}

'''
import time

DEPLOYMENT_CONFIGURATION_TYPE_MAP = {
    'maximum_percent': 'int',
    'minimum_healthy_percent': 'int'
}

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import ec2_argument_spec
from ansible.module_utils.ec2 import snake_dict_to_camel_dict, camel_dict_to_snake_dict, map_complex_type, get_ec2_security_group_ids_from_names
from ansible.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from pprint import pprint

try:
    import botocore
    import boto3
except ImportError:
    pass  # handled by AnsibleAWSModule


class ServiceDiscovery:
    """Handles route 53 Services"""


    def __init__(self, module):
        self.module = module
        self.sd = module.client('servicediscovery')

    def get_namespace(self, namespace_id):
        self.sd.get_namespace(Id= id)

    def describe_service(self, cluster_name, service_name):
        response = self.sd.get_services(
        )
        msg = ''
        if len(response['failures']) > 0:
            c = self.find_in_array(response['failures'], service_name, 'arn')
            msg += ", failure reason is " + c['reason']
            if c and c['reason'] == 'MISSING':
                return None
            # fall thru and look through found ones
        if len(response['services']) > 0:
            c = self.find_in_array(response['services'], service_name)
            if c:
                return c
        raise Exception("Unknown problem describing service %s." % service_name)

    def get_operation(self, operation_id):
        return self.sd.get_operation(operation_id)

    def create_private_dns_namespace(self, name, creator_request_id, description, vpc):
        # creator_req_id totes not needed, will be auto poulated if not given

        return self.sd.get_operation(operation_id)

    def delete_namespace(self, id):
        response = self.sd.delete_namespace(id)
        return response



    def delete_service(self, service_id):
        response = self.sd.delete_service(Id=service_id)
        # Boto returns empty dict.
        return response


    def create_service(self, name, creator_request_id, description, dns_config, health_check_config, health_check_custom_config):

        dns_records = dns_config['dns_records']
        dns_config= snake_dict_to_camel_dict(dns_config, capitalize_first=True)
        dns_config['DnsRecords']=dns_records
        health_check_config= snake_dict_to_camel_dict(health_check_config, capitalize_first=True)
        health_check_custom_config= snake_dict_to_camel_dict(health_check_custom_config, capitalize_first=True)

        params = dict(
            Name = name,
            DnsConfig = dns_config)

        if description:
            params['description']=description
        if creator_request_id:
            params['CreatorRequestId'] = creator_request_id
        if health_check_config:
            params['HealthCheckConfig']=health_check_config
        if health_check_custom_config:
            params['HealthCheckCustomConfig']=health_check_custom_config
        response = self.sd.create_service(**params)

        return self.jsonize(response['Service'])
    def get_services_by_name(self, service_name, namespace_id):
        services = self.list_services(namespace_id)
        if (not services):
          return None;
        matching_services= []
        for s in services['Services']:
            if s['Name']==service_name:
                matching_services.append(s)
        return matching_services

    def list_services(self, namespace_id):
        # namespaces suck because there's not a guarantee that they're distinct
        # I will try to make that guarantee for amazon.
        # namespaces listed will include ID, arn, name, and type

        filters = ansible_dict_to_boto3_filter_list({'NAMESPACE_ID': namespace_id})
        services = self.sd.list_services(Filters=filters)
        
        return services


    def jsonize(self, service):
        # some fields are datetime which is not JSON serializable
        # make them strings
        if 'createdAt' in service:
            service['createdAt'] = str(service['createdAt'])
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


    # Boto provides these functions:

    # can_paginate()
    # create_service()
    # delete_service()
    # deregister_instance()
    # get_instance()
    # get_instances_health_status()
    # get_operation()
    # get_paginator()
    # get_service()
    # get_waiter()
    # list_services()
    # register_instance()
    # update_instance_custom_health_status()
    # update_service()


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(required=True, choices=['present', 'absent']),
        name=dict(required=True, type='str'),
        id=dict(required=False, type='str'),
        creator_request_id=dict(required=False, type='str'),
        description=dict(required=False, type='str'),
        dns_config=dict(required=False, type='dict'),
        health_check_config=dict(required=False, type='dict'),
        health_check_custom_config=dict(required=False, type='dict'),
    ))

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=False,
                              mutually_exclusive=[['health_check_config','health_check_custom_config']]

                              )
    # TODO: there's some thought about whn to require an ID.

    sd_mgr = ServiceDiscovery(module)

    if module.params['state'] == 'present':
        try:
            service = sd_mgr.get_services_by_name(module.params['name'], module.params['dns_config']['namespace_id'])
            if (len(service) == 1):
                module.exit_json( changed=False, **camel_dict_to_snake_dict(service[0]))
            if (not service):
                service = sd_mgr.create_service(
                    module.params['name'],
                    module.params['creator_request_id'],
                    module.params['description'],
                    module.params['dns_config'],
                    module.params['health_check_config'],
                    module.params['health_check_custom_config'])
                
                module.exit_json( changed=True, **camel_dict_to_snake_dict(service))
            #TODO
        except Exception as e:
            module.fail_json(msg="Exception describing service '" + module.params['name'] +  "': " + str(e))
    if module.params['state'] == 'absent':
        try:
            service = sd_mgr.get_services_by_name(module.params['name'], module.params['dns_config']['namespace_id'])
            if (len(service) == 1):
                deletion = sd_mgr.delete_service(service[0]['Id'])
                module.exit_json( changed=True)
            else:
                module.fail_json(changed=False, msg="Failed to find service")


        except Exception as e:
            module.fail_json(msg="Exception describing service '" + module.params['name'] +  "': " + str(e))

        





if __name__ == '__main__':
    main()
