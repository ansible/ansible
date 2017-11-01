#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: route53_facts
short_description: Retrieves route53 details using AWS methods
description:
    - Gets various details related to Route53 zone, record set or health check details
version_added: "2.0"
options:
  query:
    description:
      - specifies the query action to take
    required: True
    choices: [
            'change',
            'checker_ip_range',
            'health_check',
            'hosted_zone',
            'record_sets',
            'reusable_delegation_set',
            ]
  change_id:
    description:
      - The ID of the change batch request.
        The value that you specify here is the value that
        ChangeResourceRecordSets returned in the Id element
        when you submitted the request.
    required: false
  hosted_zone_id:
    description:
      - The Hosted Zone ID of the DNS zone
    required: false
  max_items:
    description:
      - Maximum number of items to return for various get/list requests. Note that
        setting this disables pagination so don't set this any larger than around 100
    required: false
  delegation_set_id:
    description:
      - The DNS Zone delegation set ID
    required: false
  start_record_name:
    description:
      - "The first name in the lexicographic ordering of domain names that you want
        the list_command: record_sets to start listing from"
    required: false
  type:
    description:
      - The type of DNS record
    required: false
    choices: [ 'A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'CAA', 'NS' ]
  dns_name:
    description:
      - The first name in the lexicographic ordering of domain names that you want
        the list_command to start listing from
    required: false
  resource_id:
    description:
      - The ID/s of the specified resource/s
    required: false
  health_check_id:
    description:
      - The ID of the health check
    required: false
  hosted_zone_method:
    description:
      - "This is used in conjunction with query: hosted_zone.
        It allows for listing details, counts of various
        hosted zone details."
    required: false
    choices: [
        'details',
        'list',
        'list_by_name',
        'count',
        ]
    default: 'list'
  health_check_method:
    description:
      - "This is used in conjunction with query: health_check.
        It allows for listing details or counts of various
        health check details."
    required: false
    choices: [
        'list',
        'details',
        'status',
        'failure_reason',
        'count',
        ]
    default: 'list'
author: Karen Cheng(@Etherdaemon)
extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Simple example of listing all hosted zones
- name: List all hosted zones
  route53_facts:
    query: hosted_zone
  register: hosted_zones

# Getting a count of hosted zones
- name: Return a count of all hosted zones
  route53_facts:
    query: hosted_zone
    hosted_zone_method: count
  register: hosted_zone_count

- name: Get the first hosted zone called zone.example.com
  route53_facts:
    query: hosted_zone
    hosted_zone_method: list_by_name
    dns_name: zone.example.com
    max_items: 1
  register: zone_by_name

- name: List the first 20 resource record sets in a given hosted zone
  route53_facts:
    profile: account_name
    query: record_sets
    hosted_zone_id: ZZZ1111112222
    max_items: 20
  register: record_sets

- name: List first 20 health checks
  route53_facts:
    query: health_check
    health_check_method: list
    max_items: 20
  register: health_checks

- name: Get health check last failure_reason
  route53_facts:
    query: health_check
    health_check_method: failure_reason
    health_check_id: 00000000-1111-2222-3333-12345678abcd
  register: health_check_failure_reason

- name: Retrieve reusable delegation set details
  route53_facts:
    query: reusable_delegation_set
    delegation_set_id: delegation id
  register: delegation_sets
'''

RETURN = '''
delegation_set:
  description: Delegation set of name servers used by public hosted zone
  returned: when C(query) is I(hosted_zone) and C(hosted_zone_method) is I(details) and zone is public
  type: complex
  contains:
    name_servers:
      description: List of name servers
      returned: always
      type: list
      sample:
      - ns-1234.awsdns-01.com
dns_name:
  description: The value specified by C(dns_name) in the request
  returned: when C(query) is I(hosted_zone) and C(hosted_zone_method) is I(list_by_name) and C(dns_name) is specified
  type: string
  sample: host.example.com
health_check:
  description: Detail of health checks. See C(health_checks) for contents
  returned: when C(query) is I(health_check) and C(health_check_method) is I(details)
  type: dict
health_checks:
  description: List of health checks
  returned: when C(query) is I(health_check) and C(health_check_method) is I(list)
  type: complex
  contains:
    caller_reference:
      description: A unique string that is specified when the health check is created
      returned: always
      type: string
      sample: 23735269-b661-4bda-8517-df1d66cd427a
    health_check_config:
      description: Configuration of health check
      returned: always
      type: complex
      contains:
        alarm_identifier:
          description: Identifier of cloudwatch alarm
          returned: always
          type: complex
          contains:
            name:
              description: Description of cloudwatch alarm
              returned: always
              type: string
              sample: a-cloudwatch-alarm
            region:
              description: Region of cloudwatch alarm
              returned: always
              type: string
              sample: us-east-2
        insufficient_data_health_status:
          description: What to do when INSUFFICIENT_DATA is returned
          returned: always
          type: string
          sample: LastKnownStatus
        inverted:
          description: Whether the healthcheck is inverted
          returned: always
          type: bool
          sample: false
        type:
          description: Type of health check configuration
          returned: always
          type: string
          sample: CLOUDWATCH_METRIC
    health_check_version:
      description: Version of the health check
      returned: always
      type: int
      sample: 1
    id:
      description: ID of health check
      returned: always
      type: string
      sample: cf9f37f7-b188-4d63-b1fb-d59710c91412
    resource_id:
      description: Resource ID of health check
      returned: always
      type: string
      sample: cf9f37f7-b188-4d63-b1fb-d59710c91412
    resource_type:
      description: Type of resource
      returned: always
      type: string
      sample: healthcheck
    tags:
      description: Health check tags
      returned: always
      type: dict
      sample:
        name: test_health_check
health_check_count:
  description: Number of health checks
  returned: when C(query) is I(health_check) and C(health_check_method) is I(count)
  type: int
  sample: 4
hosted_zone_count:
  description: Number of hosted zones
  returned: when C(query) is I(hosted_zone) and C(hosted_zone_method) is I(count)
  type: int
  sample: 4
hosted_zone:
  description: Detail of hosted zone. See C(hosted_zone) for contents
  returned: when C(query) is I(hosted_zone) and C(hosted_zone_method) is I(details)
  type: dict
hosted_zones:
  description: List of hosted zones
  returned: when C(query) is I(hosted_zone) and C(hosted_zone_method) is I(list) or I(list_by_name)
  type: complex
  contains:
    caller_reference:
      description: Idempotency reference from hosted zone creation
      returned: always
      type: string
      sample: abcd1234-abcd-1234-abcd-123456789012
    config:
      description: Hosted zone configuration
      returned: always
      type: complex
      contains:
        comment:
          description: Comment field for the hosted zone
          returned: always
          type: string
          sample: My hosted zone
        private_zone:
          description: Whether the zone is private
          returned: always
          type: bool
          sample: true
    id:
      description: ID of hosted zone
      returned: always
      type: string
      sample: /hostedzone/Z1234ABCDEFGHI
    name:
      description: Name of hosted zone
      returned: always
      type: string
      sample: domain.example.com
    resource_record_set_count:
      description: Number of records in the zone
      returned: always
      type: int
      sample: 1234
    tags:
      description: all of the zone tags
      returned: always
      type: dict
      sample:
        Hello: World
next_dns_name:
  description: The next name that would have been returned had C(max_items) not been passed
  returned: when C(query) is I(hosted_zone) and C(hosted_zone_method) is I(list_by_name) and C(max_items) is specified
  type: string
  sample: next.example.com
next_hosted_zone_id:
  description: The hosted zone of the C(next_dns_name) returned
  returned: when C(query) is I(hosted_zone) and C(hosted_zone_method) is I(list_by_name) and C(max_items) is specified
  type: string
  sample: Z1234ABCDEFGHI
next_record_name:
  description: The name of the next record that would have been returned had C(max_items) not been passed
  returned: when C(query) is I(record_sets) and C(max_items) is specified
  type: string
  sample: next.example.com
next_record_type:
  description: The record type of the next record
  returned: when C(query) is I(record_sets) and C(max_items) is specified
  type: string
  sample: CNAME
resource_record_sets:
  description: List of Resource Record Sets
  returned: when C(query) is I(record_sets)
  type: complex
  contains:
    name:
      description: Name of the record
      returned: always
      type: string
      sample: host.example.com
    resource_records:
      description: List of resource record values
      returned: always
      type: complex
      contains:
        value:
          description: Value of the record
          returned: always
          type: string
          sample: ns-1234.awsdns-01.co.uk.
    ttl:
      description: TTL of the record
      returned: always
      type: int
      sample: 172800
    type:
      description: Resource record type
      returned: always
      type: string
      sample: NS
vpcs:
  description: List of VPCs that can use a private hosted zone
  returned: when C(query) is I(hosted_zone) and C(hosted_zone_method) is I(details) and zone is private
  type: complex
  contains:
    vpc_id:
      description: ID of the vpc
      returned: always
      type: string
      sample: vpc-abcd1234
    vpc_region:
      description: Region of the vpc
      returned: always
      type: string
      sample: us-east-2
'''

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, get_aws_connection_info
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, AWSRetry
from ansible.module_utils.ec2 import boto3_tag_list_to_ansible_dict


@AWSRetry.exponential_backoff()
def list_hosted_zones_with_backoff(client, params):
    # with max_items set, build_full_result just paginates over more
    # smaller pages - so don't paginate with max_items
    if params.get('MaxItems'):
        return client.list_hosted_zones(**params)
    else:
        paginator = client.get_paginator('list_hosted_zones')
        return paginator.paginate(**params).build_full_result()


@AWSRetry.exponential_backoff()
def list_health_check_with_backoff(client, params):
    if params.get('MaxItems'):
        return client.list_health_checks(**params)
    else:
        paginator = client.get_paginator('list_health_checks')
        return paginator.paginate(**params).build_full_result()


@AWSRetry.exponential_backoff()
def list_record_sets_with_backoff(client, params):
    if params.get('MaxItems'):
        return client.list_resource_record_sets(**params)
    else:
        paginator = client.get_paginator('list_resource_record_sets')
        return paginator.paginate(**params).build_full_result()


def get_hosted_zone(client, module):
    params = dict()

    if module.params.get('hosted_zone_id'):
        params['Id'] = module.params.get('hosted_zone_id')
    else:
        module.fail_json(msg="Hosted Zone Id is required")

    try:
        hosted_zone = client.get_hosted_zone(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get hosted zone")
    hosted_zone_id = hosted_zone['HostedZone']['Id'].replace('/hostedzone/', '')
    hosted_zone['HostedZone'].update(get_resource_tags(client, module, hosted_zone_id, 'hostedzone'))
    return hosted_zone


def reusable_delegation_set_details(client, module):
    params = dict()
    if module.params.get('delegation_set_id'):
        params['Id'] = module.params.get('delegation_set_id')
    if module.params.get('max_items'):
        params['MaxItems'] = module.params.get('max_items')
    try:
        return client.get_reusable_delegation_set(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get reusable delegation set")


def list_hosted_zones(client, module):
    params = dict()

    if module.params.get('max_items'):
        params['MaxItems'] = module.params.get('max_items')

    if module.params.get('delegation_set_id'):
        params['DelegationSetId'] = module.params.get('delegation_set_id')
    try:
        return list_hosted_zones_with_backoff(client, params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't list hosted zones")


def list_hosted_zones_by_name(client, module):
    params = dict()

    if module.params.get('hosted_zone_id'):
        params['HostedZoneId'] = module.params.get('hosted_zone_id')

    if module.params.get('dns_name'):
        params['DNSName'] = module.params.get('dns_name')

    if module.params.get('max_items'):
        params['MaxItems'] = module.params.get('max_items')

    try:
        return client.list_hosted_zones_by_name(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't list hosted zones by name")


def change_details(client, module):
    params = dict()

    if module.params.get('change_id'):
        params['Id'] = module.params.get('change_id')
    else:
        module.fail_json(msg="change_id is required")

    try:
        return client.get_change(**params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get change")


def checker_ip_range_details(client, module):
    try:
        return client.get_checker_ip_ranges()
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get checker IP ranges")


def get_count(client, module):
    if module.params.get('query') == 'health_check':
        try:
            return client.get_health_check_count()
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't get health check count")
    else:
        try:
            return client.get_hosted_zone_count()
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't get hosted zone count")


def get_health_check(client, module):
    params = dict()

    if not module.params.get('health_check_id'):
        module.fail_json(msg="health_check_id is required")
    else:
        params['HealthCheckId'] = module.params.get('health_check_id')

    if module.params.get('health_check_method') == 'failure_reason':
        try:
            return client.get_health_check_last_failure_reason(**params)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't get last health check failure reason")
    elif module.params.get('health_check_method') == 'status':
        try:
            return client.get_health_check_status(**params)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't get health check status")
    else:
        try:
            health_check = client.get_health_check(**params)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't get health check")
        health_check_id = health_check['HealthCheck']['Id']
        health_check['HealthCheck'].update(get_resource_tags(client, module, health_check_id, 'healthcheck'))
        return health_check


def get_resource_tags(client, module, resource_id, resource_type):
    try:
        result = client.list_tags_for_resource(ResourceType=resource_type, ResourceId=resource_id)['ResourceTagSet']
        result['Tags'] = boto3_tag_list_to_ansible_dict(result['Tags'])
        return result
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get resource tags")


def list_health_checks(client, module):
    params = dict()

    if module.params.get('max_items'):
        params['MaxItems'] = module.params.get('max_items')
    try:
        return list_health_check_with_backoff(client, params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't list health checks")


def record_sets_details(client, module):
    params = dict()

    if module.params.get('hosted_zone_id'):
        params['HostedZoneId'] = module.params.get('hosted_zone_id')
    else:
        module.fail_json(msg="Hosted Zone Id is required")

    if module.params.get('max_items'):
        params['MaxItems'] = module.params.get('max_items')

    if module.params.get('start_record_name'):
        params['StartRecordName'] = module.params.get('start_record_name')

    if module.params.get('type') and not module.params.get('start_record_name'):
        module.fail_json(msg="start_record_name must be specified if type is set")
    elif module.params.get('type'):
        params['StartRecordType'] = module.params.get('type')
    try:
        return list_record_sets_with_backoff(client, params)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't list record sets")


def health_check_details(client, module):
    health_check_invocations = {
        'list': list_health_checks,
        'details': get_health_check,
        'status': get_health_check,
        'failure_reason': get_health_check,
        'count': get_count,
        'tags': get_health_check,
    }

    results = health_check_invocations[module.params.get('health_check_method')](client, module)
    return results


def hosted_zone_details(client, module):
    hosted_zone_invocations = {
        'details': get_hosted_zone,
        'list': list_hosted_zones,
        'list_by_name': list_hosted_zones_by_name,
        'count': get_count,
        'tags': get_hosted_zone,
    }

    results = hosted_zone_invocations[module.params.get('hosted_zone_method')](client, module)
    return results


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        query=dict(choices=[
            'change',
            'checker_ip_range',
            'health_check',
            'hosted_zone',
            'record_sets',
            'reusable_delegation_set',
        ], required=True),
        change_id=dict(),
        hosted_zone_id=dict(),
        max_items=dict(type='str'),
        next_marker=dict(),
        delegation_set_id=dict(),
        start_record_name=dict(),
        type=dict(choices=[
            'A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'CAA', 'NS'
        ]),
        dns_name=dict(),
        resource_id=dict(type='list', aliases=['resource_ids']),
        health_check_id=dict(),
        hosted_zone_method=dict(choices=[
            'details',
            'list',
            'list_by_name',
            'count',
            'tags'
        ], default='list'),
        health_check_method=dict(choices=[
            'list',
            'details',
            'status',
            'failure_reason',
            'count',
            'tags',
        ], default='list'),
    )
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['hosted_zone_method', 'health_check_method'],
        ],
    )

    resource_id = module.params.get('resource_id')
    if resource_id:
        if len(resource_id) > 1:
            module.fail_json(msg='Using multiple resource_ids is no longer supported. Use a loop')
        module.deprecate('resource_id is deprecated. Use hosted_zone_id or health_check_id', version=2.9)
        # inject proper parameters into module.params
        if module.params.get('query') == 'hosted_zone':
            module.params['hosted_zone_id'] = '/hostedzone/%s' % resource_id[0]
        if module.params.get('query') == 'health_check':
            module.params['health_check_id'] = resource_id[0]
    if module.params.get('health_check_method') == 'tags' or module.params.get('hosted_zone_method') == 'tags':
        module.deprecate('Using tags with health_check_method or hosted_zone_method is no longer necessary - use details instead',
                         version=2.9)
    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        route53 = boto3_conn(module, conn_type='client', resource='route53', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.ProfileNotFound as e:
        module.fail_json_aws(e)

    invocations = {
        'change': change_details,
        'checker_ip_range': checker_ip_range_details,
        'health_check': health_check_details,
        'hosted_zone': hosted_zone_details,
        'record_sets': record_sets_details,
        'reusable_delegation_set': reusable_delegation_set_details,
    }
    results = invocations[module.params.get('query')](route53, module)

    # tidy up results
    for field in ['ResponseMetadata', 'MaxItems', 'IsTruncated']:
        if field in results:
            del(results[field])
    tags = results.get('Tags')

    results = camel_dict_to_snake_dict(results)
    if tags is not None:
        results['tags'] = tags

    module.exit_json(**results)


if __name__ == '__main__':
    main()
