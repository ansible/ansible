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
            - The VPC ID the zone should be a part of (if this is going to be a private zone)
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
extends_documentation_fragment: aws
author: "Christopher Troup (@minichate)"
'''

import time

try:
    import boto
    import boto.ec2
    from boto import route53
    from boto.route53 import Route53Connection
    from boto.route53.zone import Zone
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            zone=dict(required=True),
            state=dict(default='present', choices=['present', 'absent']),
            vpc_id=dict(default=None),
            vpc_region=dict(default=None),
            comment=dict(default='')))
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    zone_in = module.params.get('zone').lower()
    state = module.params.get('state').lower()
    vpc_id = module.params.get('vpc_id')
    vpc_region = module.params.get('vpc_region')
    comment = module.params.get('comment')

    private_zone = vpc_id is not None and vpc_region is not None

    _, _, aws_connect_kwargs = get_aws_connection_info(module)

    # connect to the route53 endpoint
    try:
        conn = Route53Connection(**aws_connect_kwargs)
    except boto.exception.BotoServerError, e:
        module.fail_json(msg=e.error_message)

    results = conn.get_all_hosted_zones()
    zones = {}

    for r53zone in results['ListHostedZonesResponse']['HostedZones']:
        zone_id = r53zone['Id'].replace('/hostedzone/', '')
        zone_details = conn.get_hosted_zone(zone_id)['GetHostedZoneResponse']
        if vpc_id and 'VPCs' in zone_details:
            # this is to deal with this boto bug: https://github.com/boto/boto/pull/2882
            if isinstance(zone_details['VPCs'], dict):
                if zone_details['VPCs']['VPC']['VPCId'] == vpc_id:
                    zones[r53zone['Name']] = zone_id
            else: # Forward compatibility for when boto fixes that bug
                if vpc_id in [v['VPCId'] for v in zone_details['VPCs']]:
                    zones[r53zone['Name']] = zone_id
        else:
            zones[r53zone['Name']] = zone_id

    record = {
        'private_zone': private_zone,
        'vpc_id': vpc_id,
        'vpc_region': vpc_region,
        'comment': comment,
    }

    if state == 'present' and zone_in in zones:
        if private_zone:
            details = conn.get_hosted_zone(zones[zone_in])

            if 'VPCs' not in details['GetHostedZoneResponse']:
                module.fail_json(
                    msg="Can't change VPC from public to private"
                )

            vpc_details = details['GetHostedZoneResponse']['VPCs']['VPC']
            current_vpc_id = vpc_details['VPCId']
            current_vpc_region = vpc_details['VPCRegion']

            if current_vpc_id != vpc_id:
                module.fail_json(
                    msg="Can't change VPC ID once a zone has been created"
                )
            if current_vpc_region != vpc_region:
                module.fail_json(
                    msg="Can't change VPC Region once a zone has been created"
                )

        record['zone_id'] = zones[zone_in]
        record['name'] = zone_in
        module.exit_json(changed=False, set=record)

    elif state == 'present':
        result = conn.create_hosted_zone(zone_in, **record)
        hosted_zone = result['CreateHostedZoneResponse']['HostedZone']
        zone_id = hosted_zone['Id'].replace('/hostedzone/', '')
        record['zone_id'] = zone_id
        record['name'] = zone_in
        module.exit_json(changed=True, set=record)

    elif state == 'absent' and zone_in in zones:
        conn.delete_hosted_zone(zones[zone_in])
        module.exit_json(changed=True)

    elif state == 'absent':
        module.exit_json(changed=False)

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
