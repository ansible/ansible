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
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: route53_zone
short_description: add or delete Route53 zones
description:
    - Creates and deletes Route53 private and public zones
version_added: "2.0"
requirements: [ boto3 ]
options:
    zone:
        description:
            - "The DNS zone record (eg: foo.com.)"
        required: true
    state:
        description:
            - whether or not the zone should exist or not
        default: present
        choices: [ "present", "absent" ]
    vpc_id:
        description:
            - The VPC ID the zone should be a part of (if this is going to be a private zone)
    vpc_region:
        description:
            - The VPC Region the zone should be a part of (if this is going to be a private zone)
    comment:
        description:
            - Comment associated with the zone
        default: ''
    hosted_zone_id:
        description:
            - The unique zone identifier you want to delete or "all" if there are many zones with the same domain name.
              Required if there are multiple zones identified with the above options
        version_added: 2.4
    delegation_set_id:
        description:
            - The reusable delegation set ID to be associated with the zone.
              Note that you can't associate a reusable delegation set with a private hosted zone.
        version_added: 2.6
extends_documentation_fragment:
    - aws
    - ec2
author: "Christopher Troup (@minichate)"
'''

EXAMPLES = '''
- name: create a public zone
  route53_zone:
    zone: example.com
    comment: this is an example

- name: delete a public zone
  route53_zone:
    zone: example.com
    state: absent

- name: create a private zone
  route53_zone:
    zone: devel.example.com
    vpc_id: '{{ myvpc_id }}'
    vpc_region: us-west-2
    comment: developer domain

- name: create a public zone associated with a specific reusable delegation set
  route53_zone:
    zone: example.com
    comment: reusable delegation set example
    delegation_set_id: A1BCDEF2GHIJKL
'''

RETURN = '''
comment:
    description: optional hosted zone comment
    returned: when hosted zone exists
    type: string
    sample: "Private zone"
name:
    description: hosted zone name
    returned: when hosted zone exists
    type: string
    sample: "private.local."
private_zone:
    description: whether hosted zone is private or public
    returned: when hosted zone exists
    type: bool
    sample: true
vpc_id:
    description: id of vpc attached to private hosted zone
    returned: for private hosted zone
    type: string
    sample: "vpc-1d36c84f"
vpc_region:
    description: region of vpc attached to private hosted zone
    returned: for private hosted zone
    type: string
    sample: "eu-west-1"
zone_id:
    description: hosted zone id
    returned: when hosted zone exists
    type: string
    sample: "Z6JQG9820BEFMW"
delegation_set_id:
    description: id of the associated reusable delegation set
    returned: for public hosted zones, if they have been associated with a reusable delegation set
    type: string
    sample: "A1BCDEF2GHIJKL"
'''

import time
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, get_aws_connection_info

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule


def find_zones(module, client, zone_in, private_zone):
    try:
        paginator = client.get_paginator('list_hosted_zones')
        results = paginator.paginate().build_full_result()
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Could not list current hosted zones")
    zones = []
    for r53zone in results['HostedZones']:
        if r53zone['Name'] != zone_in:
            continue
        # only save zone names that match the public/private setting
        if (r53zone['Config']['PrivateZone'] and private_zone) or \
           (not r53zone['Config']['PrivateZone'] and not private_zone):
            zones.append(r53zone)

    return zones


def create(module, client, matching_zones):
    zone_in = module.params.get('zone').lower()
    vpc_id = module.params.get('vpc_id')
    vpc_region = module.params.get('vpc_region')
    comment = module.params.get('comment')
    delegation_set_id = module.params.get('delegation_set_id')

    if not zone_in.endswith('.'):
        zone_in += "."

    private_zone = bool(vpc_id and vpc_region)

    record = {
        'private_zone': private_zone,
        'vpc_id': vpc_id,
        'vpc_region': vpc_region,
        'comment': comment,
        'name': zone_in,
        'delegation_set_id': delegation_set_id,
    }

    if private_zone:
        changed, result = create_or_update_private(module, client, matching_zones, record)
    else:
        changed, result = create_or_update_public(module, client, matching_zones, record)

    return changed, result


def create_or_update_private(module, client, matching_zones, record):
    for z in matching_zones:
        try:
            result = client.get_hosted_zone(Id=z['Id'])  # could be in different regions or have different VPCids
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Could not get details about hosted zone %s" % z['Id'])
        zone_details = result['HostedZone']
        vpc_details = result['VPCs']
        current_vpc_id = None
        current_vpc_region = None
        if isinstance(vpc_details, dict):
            if vpc_details['VPC']['VPCId'] == record['vpc_id']:
                current_vpc_id = vpc_details['VPC']['VPCId']
                current_vpc_region = vpc_details['VPC']['VPCRegion']
        else:
            if record['vpc_id'] in [v['VPCId'] for v in vpc_details]:
                current_vpc_id = record['vpc_id']
                if record['vpc_region'] in [v['VPCRegion'] for v in vpc_details]:
                    current_vpc_region = record['vpc_region']

        if record['vpc_id'] == current_vpc_id and record['vpc_region'] == current_vpc_region:
            record['zone_id'] = zone_details['Id'].replace('/hostedzone/', '')
            if 'Comment' in zone_details['Config'] and zone_details['Config']['Comment'] != record['comment']:
                if not module.check_mode:
                    try:
                        client.update_hosted_zone_comment(Id=zone_details['Id'], Comment=record['comment'])
                    except (BotoCoreError, ClientError) as e:
                        module.fail_json_aws(e, msg="Could not update comment for hosted zone %s" % zone_details['Id'])
                return True, record
            else:
                record['msg'] = "There is already a private hosted zone in the same region with the same VPC \
                    you chose. Unable to create a new private hosted zone in the same name space."
                return False, record

    if not module.check_mode:
        try:
            result = client.create_hosted_zone(
                Name=record['name'],
                HostedZoneConfig={
                    'Comment': record['comment'] if record['comment'] is not None else "",
                    'PrivateZone': True,
                },
                VPC={
                    'VPCRegion': record['vpc_region'],
                    'VPCId': record['vpc_id'],
                },
                CallerReference="%s-%s" % (record['name'], time.time()),
            )
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Could not create hosted zone")

        hosted_zone = result['HostedZone']
        zone_id = hosted_zone['Id'].replace('/hostedzone/', '')
        record['zone_id'] = zone_id

    changed = True
    return changed, record


def create_or_update_public(module, client, matching_zones, record):
    zone_details, zone_delegation_set_details = None, {}
    for matching_zone in matching_zones:
        try:
            zone = client.get_hosted_zone(Id=matching_zone['Id'])
            zone_details = zone['HostedZone']
            zone_delegation_set_details = zone.get('DelegationSet', {})
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Could not get details about hosted zone %s" % matching_zone['Id'])
        if 'Comment' in zone_details['Config'] and zone_details['Config']['Comment'] != record['comment']:
            if not module.check_mode:
                try:
                    client.update_hosted_zone_comment(
                        Id=zone_details['Id'],
                        Comment=record['comment']
                    )
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg="Could not update comment for hosted zone %s" % zone_details['Id'])
            changed = True
        else:
            changed = False
        break

    if zone_details is None:
        if not module.check_mode:
            try:
                params = dict(
                    Name=record['name'],
                    HostedZoneConfig={
                        'Comment': record['comment'] if record['comment'] is not None else "",
                        'PrivateZone': False,
                    },
                    CallerReference="%s-%s" % (record['name'], time.time()),
                )

                if record.get('delegation_set_id') is not None:
                    params['DelegationSetId'] = record['delegation_set_id']

                result = client.create_hosted_zone(**params)
                zone_details = result['HostedZone']
                zone_delegation_set_details = result.get('DelegationSet', {})

            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Could not create hosted zone")
        changed = True

    if not module.check_mode:
        record['zone_id'] = zone_details['Id'].replace('/hostedzone/', '')
        record['name'] = zone_details['Name']
        record['delegation_set_id'] = zone_delegation_set_details.get('Id', '').replace('/delegationset/', '')

    return changed, record


def delete_private(module, client, matching_zones, vpc_id, vpc_region):
    for z in matching_zones:
        try:
            result = client.get_hosted_zone(Id=z['Id'])
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Could not get details about hosted zone %s" % z['Id'])
        zone_details = result['HostedZone']
        vpc_details = result['VPCs']
        if isinstance(vpc_details, dict):
            if vpc_details['VPC']['VPCId'] == vpc_id and vpc_region == vpc_details['VPC']['VPCRegion']:
                if not module.check_mode:
                    try:
                        client.delete_hosted_zone(Id=z['Id'])
                    except (BotoCoreError, ClientError) as e:
                        module.fail_json_aws(e, msg="Could not delete hosted zone %s" % z['Id'])
                return True, "Successfully deleted %s" % zone_details['Name']
        else:
            if vpc_id in [v['VPCId'] for v in vpc_details] and vpc_region in [v['VPCRegion'] for v in vpc_details]:
                if not module.check_mode:
                    try:
                        client.delete_hosted_zone(Id=z['Id'])
                    except (BotoCoreError, ClientError) as e:
                        module.fail_json_aws(e, msg="Could not delete hosted zone %s" % z['Id'])
                return True, "Successfully deleted %s" % zone_details['Name']

    return False, "The vpc_id and the vpc_region do not match a private hosted zone."


def delete_public(module, client, matching_zones):
    if len(matching_zones) > 1:
        changed = False
        msg = "There are multiple zones that match. Use hosted_zone_id to specify the correct zone."
    else:
        if not module.check_mode:
            try:
                client.delete_hosted_zone(Id=matching_zones[0]['Id'])
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Could not get delete hosted zone %s" % matching_zones[0]['Id'])
        changed = True
        msg = "Successfully deleted %s" % matching_zones[0]['Id']
    return changed, msg


def delete_hosted_id(module, client, hosted_zone_id, matching_zones):
    if hosted_zone_id == "all":
        deleted = []
        for z in matching_zones:
            deleted.append(z['Id'])
            if not module.check_mode:
                try:
                    client.delete_hosted_zone(Id=z['Id'])
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg="Could not delete hosted zone %s" % z['Id'])
        changed = True
        msg = "Successfully deleted zones: %s" % deleted
    elif hosted_zone_id in [zo['Id'].replace('/hostedzone/', '') for zo in matching_zones]:
        if not module.check_mode:
            try:
                client.delete_hosted_zone(Id=hosted_zone_id)
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Could not delete hosted zone %s" % hosted_zone_id)
        changed = True
        msg = "Successfully deleted zone: %s" % hosted_zone_id
    else:
        changed = False
        msg = "There is no zone to delete that matches hosted_zone_id %s." % hosted_zone_id
    return changed, msg


def delete(module, client, matching_zones):
    zone_in = module.params.get('zone').lower()
    vpc_id = module.params.get('vpc_id')
    vpc_region = module.params.get('vpc_region')
    hosted_zone_id = module.params.get('hosted_zone_id')

    if not zone_in.endswith('.'):
        zone_in += "."

    private_zone = bool(vpc_id and vpc_region)

    if zone_in in [z['Name'] for z in matching_zones]:
        if hosted_zone_id:
            changed, result = delete_hosted_id(module, client, hosted_zone_id, matching_zones)
        else:
            if private_zone:
                changed, result = delete_private(module, client, matching_zones, vpc_id, vpc_region)
            else:
                changed, result = delete_public(module, client, matching_zones)
    else:
        changed = False
        result = "No zone to delete."

    return changed, result


def main():
    argument_spec = dict(
        zone=dict(required=True),
        state=dict(default='present', choices=['present', 'absent']),
        vpc_id=dict(default=None),
        vpc_region=dict(default=None),
        comment=dict(default=''),
        hosted_zone_id=dict(),
        delegation_set_id=dict(),
    )

    mutually_exclusive = [
        ['delegation_set_id', 'vpc_id'],
        ['delegation_set_id', 'vpc_region'],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=mutually_exclusive,
        supports_check_mode=True,
    )

    zone_in = module.params.get('zone').lower()
    state = module.params.get('state').lower()
    vpc_id = module.params.get('vpc_id')
    vpc_region = module.params.get('vpc_region')

    if not zone_in.endswith('.'):
        zone_in += "."

    private_zone = bool(vpc_id and vpc_region)

    client = module.client('route53')

    zones = find_zones(module, client, zone_in, private_zone)
    if state == 'present':
        changed, result = create(module, client, matching_zones=zones)
    elif state == 'absent':
        changed, result = delete(module, client, matching_zones=zones)

    if isinstance(result, dict):
        module.exit_json(changed=changed, result=result, **result)
    else:
        module.exit_json(changed=changed, result=result)


if __name__ == '__main__':
    main()
