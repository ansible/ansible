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
module: service_discovery_registry
short_description: thin wrap for boto servicediscovery client
description:
    - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/servicediscovery.html
    - service discovery comes in two parts, a namespace and a service discovery "registry"
    - Namespace is somewhat owned by route53
    - Registries are owned by the namespace
    - ECS containers may announce themselves to the registry
    - There may be other things that use registries
    - This module tries to allow creating service discovery registries
notes:
    - currently, public namespaces have not been tested.
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
            A unique string that identifies the request and that allows failed CreateService requests to be retried without
            the risk of executing the operation twice. CreatorRequestId can be any unique string, for example, a date/time stamp.
            This field is autopopulated if not provided.
        required: false
    description:
        description: Description for the service.
    dns_config:
        required: True
        description:
            A complex type that contains information about the records that you want Route 53 to create
            when you register an instance.
        suboptions:
            namespace_id:
                description: ID of the service discovery namespace you will associate this service with
            routing_policy:
                description:
                    The routing policy that you want to apply to all records that Route 53 creates when
                    you register an instance and specify this service.
                suboptions:
                    dns_records:
                        description:
                            complex type describing what type of dns record will be created when a service registers
                        suboptions:
                            type:
                                description: SRV|A|AAAA|CNAME
                            ttl:
                                description: How long the record will live
    health_check_config:
        required: false
        description:  Required when service discovery namespace is public
        suboptions:
            failure_threshold:
                description:
                    The number of consecutive health checks that an endpoint must pass or fail for Route 53
                    to change the current status of the endpoint from unhealthy to healthy or vice versa.
            type:
                description: Health check type ( 'HTTP'|'HTTPS'|'TCP' )
            resource_path:
                description: The path that you want Route 53 to request when performing health checks.

    health_check_custom_config:
        required: False
        description: Required when service discovery namespace is private
        suboptions:
            failure_threshold:
                description:
                    The number of consecutive health checks that an endpoint must pass or fail for Route 53
                    to change the current status of the endpoint from unhealthy to healthy or vice versa.

extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

Private:
  - service_discovery_registry:
      name: "sd-example" # becomes sd-example.your-private-sd-namespace.
      state: "present"
      dns_config:
        namespace_id: "namespace_id"
        routing_policy: "WEIGHTED"
        dns_records:
          - Type: "SRV"
            TTL: 60
      health_check_custom_config:
        failure_threshold: 1
Public:
  - service_discovery_registry:
      name: "sd-example" # becomes sd-example.your-public-sd-namespace.tld
      state: "present"
      dns_config:
        namespace_id: "namespace_id"
        routing_policy: "WEIGHTED"
        dns_records:
          - Type: "SRV"
            TTL: 60
      health_check_config:
          Type: "HTTP"
          ResourcePath: "/health-check"
          FailureThreshold: 2
'''

RETURN = '''
service:
    description: Details of created service.
    returned: when creating a service
    type: complex
    contains:
        id:
            description: Identifier of service discovery service
            returned: always
            type: string
        arn:
            description: arn of service discovery service
            returned: always
            type: string
        name:
            description: name of service discovery service
            returned: always
            type: string
        description:
            description: description of service discovery service
            returned: always
            type: string
        instance_count:
            description:
                The number of instances that are currently associated with the service. Instances that were
                previously associated with the service but that have been deleted are not included in the count.
            returned: always
            type: int
        dns_config:
            description: A complex type that contains information about the records that you want Route 53 to create when you register an instance.
            returned: always
            type: complex
            contains:
                namespace_id:
                    description: The ID of the namespace to use for DNS configuration.
                    type: string
                    returned: always
                routing_policy:
                    description:
                        The routing policy that you want to apply to all records that Route 53
                        creates when you register an instance and specify this service. (MULTIVALUE|WEIGHTED)
                    type: string
                    returned: always
                dns_records:
                    description:
                        An array that contains one DnsRecord object for each record that you want Route 53
                        to create when you register an instance.
                    type: complex
                    contains:
                        type:
                            description:
                                The type of the resource, which indicates the type of value that Route 53
                                returns in response to DNS queries.
                            type: string
                            returned: always
                        ttl:
                            description:
                                The type of the resource, which indicates the type of value that Route 53
                                returns in response to DNS queries.
                            type: int
                            returned: always
        health_check_custom_config:
            type: complex
            returned: when service discovery namespace is dns_private type
            contains:
                failure_threshold:
                    description:
                        The number of consecutive health checks that an endpoint must pass or fail for Route 53
                        to change the current status of the endpoint from unhealthy to healthy or vice versa.
                    type: int
                    returned: always
        health_check_config:
            type: complex
            returned: when service discovery namespace is dns_public type
            contains:
                failure_threshold:
                    description:
                        The number of consecutive health checks that an endpoint must pass or fail for Route 53
                        to change the current status of the endpoint from unhealthy to healthy or vice versa.
                    type: int
                    returned: always
                resource_path:
                    description: The path that you want Route 53 to request when performing health checks.
                    type: string
                    returned: always
                type:
                    type: string
                    returned: always
                    description: The type of health check that you want to create, which indicates how Route 53 determines whether an endpoint is healthy.
        create_date:
            type: datetime
            returned: always
            description: datetime of creation
        creator_request_id:
            type: string
            returned: always
            description:
                A unique string that identifies the request and that allows failed requests to be retried without
                the risk of executing an operation twice.
'''
import time


from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import ec2_argument_spec
from ansible.module_utils.ec2 import snake_dict_to_camel_dict, camel_dict_to_snake_dict, map_complex_type, get_ec2_security_group_ids_from_names
from ansible.module_utils.ec2 import ansible_dict_to_boto3_filter_list

try:
    import botocore
except ImportError:
    pass


class ServiceDiscoveryRegistry:
    """Handles Service discovery registries"""

    def __init__(self, module):
        self.module = module
        self.sd = module.client('servicediscovery')

    def get_namespace(self, namespace_id):
        self.sd.get_namespace(Id=id)

    def get_service(self, service_id):
        response = self.sd.get_service(Id=service_id)
        if response['Service']:
            return self.jsonize(response['Service'])
        else:
            return None

    def get_operation(self, operation_id):
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
        dns_config = snake_dict_to_camel_dict(dns_config, capitalize_first=True)
        dns_config['DnsRecords'] = []
        # use correct casing for aws api
        for c in dns_records:
            dns_config['DnsRecords'].append({'Type': c['type'], 'TTL': c['ttl']})
        health_check_config = snake_dict_to_camel_dict(health_check_config, capitalize_first=True)
        health_check_custom_config = snake_dict_to_camel_dict(health_check_custom_config, capitalize_first=True)

        params = dict(
            Name=name,
            DnsConfig=dns_config)

        if description:
            params['description'] = description
        if creator_request_id:
            params['CreatorRequestId'] = creator_request_id
        if health_check_config:
            params['HealthCheckConfig'] = health_check_config

        if health_check_custom_config:
            params['HealthCheckCustomConfig'] = health_check_custom_config
        response = self.sd.create_service(**params)
        return self.jsonize(response['Service'])

    def get_services_by_name(self, service_name, namespace_id):
        services = self.list_services(namespace_id)
        if (not services):
            return None
        matching_services = []
        for s in services['Services']:
            if s['Name'] == service_name:
                matching_services.append(s)
        return matching_services

    def list_services(self, namespace_id):
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


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(required=True, choices=['present', 'absent']),
        name=dict(required=True, type='str'),
        creator_request_id=dict(required=False, type='str'),
        description=dict(required=False, type='str'),
        dns_config=dict(required=False, type='dict'),
        health_check_config=dict(required=False, type='dict'),
        health_check_custom_config=dict(required=False, type='dict'),
    ))

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=False,
                              mutually_exclusive=[['health_check_config', 'health_check_custom_config']],
                              required_if=[('state', 'present', ['name', 'dns_config'])]
                              )
# TODO: There's no real use for ID right now, but you should be able to delete a registry by id

    sd_mgr = ServiceDiscoveryRegistry(module)

    if module.params['state'] == 'present':
        try:
            changed = False
            service = sd_mgr.get_services_by_name(module.params['name'], module.params['dns_config']['namespace_id'])
            # service returned by get_services_by_name includes Id, Name, Arn only
            if (len(service) == 1):
                # if a service was found, use get_service to get the full info
                service = sd_mgr.get_service(service[0]['Id'])
            if (not service):
                service = sd_mgr.create_service(
                    module.params['name'],
                    module.params['creator_request_id'],
                    module.params['description'],
                    module.params['dns_config'],
                    module.params['health_check_config'],
                    module.params['health_check_custom_config'])
                changed = True
                # service returned by sd_mgr is already unwrapped dict;
            module.exit_json(changed=changed, service=camel_dict_to_snake_dict(service))

        except Exception as e:
            module.fail_json(msg="Exception for servicediscovery '" + module.params['name'] + "': " + str(e))
    if module.params['state'] == 'absent':
        try:
            service = sd_mgr.get_services_by_name(module.params['name'], module.params['dns_config']['namespace_id'])
            if (len(service) == 1):
                deletion = sd_mgr.delete_service(service[0]['Id'])
                module.exit_json(changed=True)
            else:
                module.fail_json(changed=False, msg="Failed to find service")
        except Exception as e:
            module.fail_json(msg="Exception for servicediscovery '" + module.params['name'] + "': " + str(e))


if __name__ == '__main__':
    main()
