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
      - Maximum number of items to return for various get/list requests
    required: false
  next_marker:
    description:
      - "Some requests such as list_command: hosted_zones will return a maximum
        number of entries - EG 100 or the number specified by max_items.
        If the number of entries exceeds this maximum another request can be sent
        using the NextMarker entry from the first response to get the next page
        of results"
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
    aliases: ['resource_ids']
  health_check_id:
    description:
      - The ID of the health check
    required: false
  hosted_zone_method:
    description:
      - "This is used in conjunction with query: hosted_zone.
        It allows for listing details, counts or tags of various
        hosted zone details."
    required: false
    choices: [
        'details',
        'list',
        'list_by_name',
        'count',
        'tags',
        ]
    default: 'list'
  health_check_method:
    description:
      - "This is used in conjunction with query: health_check.
        It allows for listing details, counts or tags of various
        health check details."
    required: false
    choices: [
        'list',
        'details',
        'status',
        'failure_reason',
        'count',
        'tags',
        ]
    default: 'list'
author: Karen Cheng(@Etherdaemon)
extends_documentation_fragment:
  - aws
  - ec2
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

- name: setup of example for using next_marker
  route53_facts:
    query: hosted_zone
    max_items: 1
  register: first_facts
- name: example for using next_marker
  route53_facts:
    query: hosted_zone
    next_marker: "{{ first_facts.NextMarker }}"
    max_items: 1
  when: "{{ 'NextMarker' in first_facts }}"
'''
try:
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, get_aws_connection_info


def get_hosted_zone(client, module):
    params = dict()

    if module.params.get('hosted_zone_id'):
        params['Id'] = module.params.get('hosted_zone_id')
    else:
        module.fail_json(msg="Hosted Zone Id is required")

    results = client.get_hosted_zone(**params)
    return results


def reusable_delegation_set_details(client, module):
    params = dict()
    if not module.params.get('delegation_set_id'):
        if module.params.get('max_items'):
            params['MaxItems'] = module.params.get('max_items')

        if module.params.get('next_marker'):
            params['Marker'] = module.params.get('next_marker')

        results = client.list_reusable_delegation_sets(**params)
    else:
        params['DelegationSetId'] = module.params.get('delegation_set_id')
        results = client.get_reusable_delegation_set(**params)

    return results


def list_hosted_zones(client, module):
    params = dict()

    if module.params.get('max_items'):
        params['MaxItems'] = module.params.get('max_items')

    if module.params.get('next_marker'):
        params['Marker'] = module.params.get('next_marker')

    if module.params.get('delegation_set_id'):
        params['DelegationSetId'] = module.params.get('delegation_set_id')

    results = client.list_hosted_zones(**params)
    return results


def list_hosted_zones_by_name(client, module):
    params = dict()

    if module.params.get('hosted_zone_id'):
        params['HostedZoneId'] = module.params.get('hosted_zone_id')

    if module.params.get('dns_name'):
        params['DNSName'] = module.params.get('dns_name')

    if module.params.get('max_items'):
        params['MaxItems'] = module.params.get('max_items')

    results = client.list_hosted_zones_by_name(**params)
    return results


def change_details(client, module):
    params = dict()

    if module.params.get('change_id'):
        params['Id'] = module.params.get('change_id')
    else:
        module.fail_json(msg="change_id is required")

    results = client.get_change(**params)
    return results


def checker_ip_range_details(client, module):
    results = client.get_checker_ip_ranges()
    return results


def get_count(client, module):
    if module.params.get('query') == 'health_check':
        results = client.get_health_check_count()
    else:
        results = client.get_hosted_zone_count()

    return results


def get_health_check(client, module):
    params = dict()

    if not module.params.get('health_check_id'):
        module.fail_json(msg="health_check_id is required")
    else:
        params['HealthCheckId'] = module.params.get('health_check_id')

    if module.params.get('health_check_method') == 'details':
        results = client.get_health_check(**params)
    elif module.params.get('health_check_method') == 'failure_reason':
        results = client.get_health_check_last_failure_reason(**params)
    elif module.params.get('health_check_method') == 'status':
        results = client.get_health_check_status(**params)

    return results


def get_resource_tags(client, module):
    params = dict()

    if module.params.get('resource_id'):
        params['ResourceIds'] = module.params.get('resource_id')
    else:
        module.fail_json(msg="resource_id or resource_ids is required")

    if module.params.get('query') == 'health_check':
        params['ResourceType'] = 'healthcheck'
    else:
        params['ResourceType'] = 'hostedzone'

    results = client.list_tags_for_resources(**params)
    return results


def list_health_checks(client, module):
    params = dict()

    if module.params.get('max_items'):
        params['MaxItems'] = module.params.get('max_items')

    if module.params.get('next_marker'):
        params['Marker'] = module.params.get('next_marker')

    results = client.list_health_checks(**params)
    return results


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

    results = client.list_resource_record_sets(**params)
    return results


def health_check_details(client, module):
    health_check_invocations = {
        'list': list_health_checks,
        'details': get_health_check,
        'status': get_health_check,
        'failure_reason': get_health_check,
        'count': get_count,
        'tags': get_resource_tags,
    }

    results = health_check_invocations[module.params.get('health_check_method')](client, module)
    return results


def hosted_zone_details(client, module):
    hosted_zone_invocations = {
        'details': get_hosted_zone,
        'list': list_hosted_zones,
        'list_by_name': list_hosted_zones_by_name,
        'count': get_count,
        'tags': get_resource_tags,
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

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['hosted_zone_method', 'health_check_method'],
        ],
    )

    # Validate Requirements
    if not (HAS_BOTO or HAS_BOTO3):
        module.fail_json(msg='json and boto/boto3 is required.')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        route53 = boto3_conn(module, conn_type='client', resource='route53', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except boto.exception.NoAuthHandlerFound as e:
        module.fail_json(msg="Can't authorize connection - %s " % str(e))

    invocations = {
        'change': change_details,
        'checker_ip_range': checker_ip_range_details,
        'health_check': health_check_details,
        'hosted_zone': hosted_zone_details,
        'record_sets': record_sets_details,
        'reusable_delegation_set': reusable_delegation_set_details,
    }
    results = invocations[module.params.get('query')](route53, module)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
