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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: route53_zone
short_description: add or delete Route53 zones
description:
    - Creates and deletes Route53 private and public zones
version_added: "2.0"
options:
    zone:
        description:
            - "The DNS zone record (eg: foo.com.)"
        required: true
    state:
        description:
            - whether or not the zone should exist or not
        required: false
        default: true
        choices: [ "present", "absent" ]
    vpc_id:
        description:
            - One or more VPC IDs that the zone should be associated with (if this is going to be a private zone)
              Multiple VPCs are only supported since 2.3.
        required: false
        default: null
    vpc_region:
        description:
            - The VPC Region the zone should be a part of (if this is going to be a private zone)
        required: false
        default: null
    comment:
        description:
            - Comment associated with the zone
        required: false
        default: ''
extends_documentation_fragment:
    - aws
    - ec2
author: "Christopher Troup (@minichate)"
'''

EXAMPLES = '''
# create a public zone
- route53_zone:
    zone: example.com
    state: present
    comment: this is an example

# delete a public zone
- route53_zone:
    zone: example.com
    state: absent

- name: private zone for devel
  route53_zone:
    zone: devel.example.com
    state: present
    vpc_id: '{{ myvpc_id }}'
    comment: developer domain private zone for devel

- name: associate a zone with multiple VPCs
  route53_zone:
    zone: devel.example.com
    state: present
    vpc_id:
      - vpc-abcd1234
      - vpc-abbad0d0
    comment: developer domain

# more complex example
- name: register output after creating zone in parameterized region
  route53_zone:
    vpc_id: '{{ vpc.vpc_id }}'
    vpc_region: '{{ ec2_region }}'
    zone: '{{ vpc_dns_zone }}'
    state: present
  register: zone_out

- debug:
    var: zone_out
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
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info
from ansible.module_utils.ec2 import boto3_conn, HAS_BOTO3, camel_dict_to_snake_dict

try:
    import botocore
except ImportError:
    pass  # caught by imported HAS_BOTO3

import traceback
import uuid


def update_vpc_associations(module, conn, zone, current_vpcs, desired_vpcs):
    _, _, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    vpc_region = module.params.get('vpc_region')
    for vpc in desired_vpcs - current_vpcs:
        try:
            conn.associate_vpc_with_hosted_zone(HostedZoneId=zone['Id'].replace('/hostedzone/', ''),
                                                VPC=dict(VPCRegion=vpc_region,
                                                         VPCId=vpc))
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Couldn't associate VPC %s with zone %s: %s" % (vpc, zone['Name'], str(e)),
                             exception=traceback.format_exc(e), **camel_dict_to_snake_dict(e.response))
    for vpc in current_vpcs - desired_vpcs:
        try:
            conn.disassociate_vpc_from_hosted_zone(HostedZoneId=zone['Id'].replace('/hostedzone/', ''),
                                                   VPC=dict(VPCRegion=vpc_region,
                                                            VPCId=vpc))
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Couldn't disassociate VPC %s from zone %s: %s" % (vpc, zone['Name'], str(e)),
                             exception=traceback.format_exc(e), **camel_dict_to_snake_dict(e.response))


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            zone=dict(required=True),
            state=dict(default='present', choices=['present', 'absent']),
            vpc_id=dict(type='list', default=[]),
            vpc_region=dict(),
            comment=dict(default='')
        )
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    if not HAS_BOTO3:
        module.fail_json("boto3 and botocore are required for route53_zone module")

    zone_in = module.params.get('zone').lower()
    state = module.params.get('state').lower()
    vpc_id = module.params.get('vpc_id')
    vpc_region = module.params.get('vpc_region')
    comment = module.params.get('comment')

    if zone_in[-1:] != '.':
        zone_in += "."

    private_zone = vpc_id is not None and vpc_region is not None

    _, _, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    conn = boto3_conn(module, conn_type='client', resource='route53',
                      **aws_connect_kwargs)

    results = conn.list_hosted_zones()
    zones = {}

    for r53zone in results['HostedZones']:
        zone_id = r53zone['Id'].replace('/hostedzone/', '')
        zones[r53zone['Name']] = zone_id

    if vpc_id:
        desired_vpcs = set(vpc_id)

    record = {
        'private_zone': private_zone,
        'vpc_id': vpc_id[0],
        'vpc_region': vpc_region,
        'comment': comment,
    }

    if state == 'present' and zone_in in zones:
        if private_zone:
            details = conn.get_hosted_zone(Id=zones[zone_in])
            changed = False

            if not details['HostedZone']['Config']['PrivateZone']:
                module.fail_json(
                    msg="Can't change VPC from public to private"
                )

            desired_vpcs = set(vpc_id)
            current_vpc_region = details['VPCs'][0]['VPCRegion']
            current_vpcs = set([v['VPCId'] for v in details['VPCs']])

            if current_vpc_region != vpc_region:
                module.fail_json(msg="Can't change VPC Region once a zone has been created")

            if current_vpcs != desired_vpcs:
                update_vpc_associations(module, conn, details['HostedZone'], current_vpcs, desired_vpcs)
                changed = True

        record['zone_id'] = zones[zone_in]
        record['name'] = zone_in
        record['vpc_id'] = ','.join(desired_vpcs)
        module.exit_json(changed=changed, set=record)

    elif state == 'present':
        params = dict(Name=zone_in, HostedZoneConfig=dict(Comment=comment, PrivateZone=private_zone),
                      CallerReference=str(uuid.uuid4()))
        if private_zone:
            params['VPC'] = dict(VPCRegion=vpc_region, VPCId=vpc_id[0])
        if not module.check_mode:
            result = conn.create_hosted_zone(**params)
            hosted_zone = result['HostedZone']
            zone_id = hosted_zone['Id'].replace('/hostedzone/', '')
            record['zone_id'] = zone_id
        record['name'] = zone_in
        if len(desired_vpcs) > 1:
            current_vpcs = set([vpc_id[0]])
            update_vpc_associations(module, conn, hosted_zone, current_vpcs, desired_vpcs)
            record['vpc_id'] = ','.join(desired_vpcs)

        module.exit_json(changed=True, set=record)

    elif state == 'absent' and zone_in in zones:
        if not module.check_mode:
            conn.delete_hosted_zone(zones[zone_in])
        module.exit_json(changed=True)

    elif state == 'absent':
        module.exit_json(changed=False)

if __name__ == '__main__':
    main()
