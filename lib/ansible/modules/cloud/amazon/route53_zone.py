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
options:
    zone:
        description:
            - "The DNS zone record (eg: foo.com.)"
        required: true
    state:
        description:
            - whether or not the zone should exist or not
        required: false
        default: present
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
    hosted_zone_id:
        description:
            - The unique zone identifier you want to delete or "all" if there are many zones with the same domain name.
              Required if there are multiple zones identified with the above options
        required: false
        default: null
        version_added: 2.4
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

try:
    import boto
    from boto.route53 import Route53Connection
    from boto.route53.zone import Zone
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info


def find_zones(conn, zone_in, private_zone):
    results = conn.get_all_hosted_zones()
    zones = {}
    for r53zone in results['ListHostedZonesResponse']['HostedZones']:
        if r53zone['Name'] != zone_in:
            continue
        # only save zone names that match the public/private setting
        if r53zone['Config']['PrivateZone'] == 'true' and private_zone:
            zones[r53zone.get('Id', '').replace('/hostedzone/', '')] = r53zone['Name']
        if r53zone['Config']['PrivateZone'] == 'false' and not private_zone:
            zones[r53zone.get('Id', '').replace('/hostedzone/', '')] = r53zone['Name']

    return zones


def create(conn, module, matching_zones):
    zone_in = module.params.get('zone').lower()
    vpc_id = module.params.get('vpc_id')
    vpc_region = module.params.get('vpc_region')
    comment = module.params.get('comment')

    if not zone_in.endswith('.'):
        zone_in += "."

    private_zone = bool(vpc_id and vpc_region)

    record = {
        'private_zone': private_zone,
        'vpc_id': vpc_id,
        'vpc_region': vpc_region,
        'comment': comment,
    }

    if private_zone:
        changed, result = create_private(conn, matching_zones, vpc_id, vpc_region, zone_in, record)
    else:
        changed, result = create_public(conn, matching_zones, zone_in, record)

    return changed, result


def create_private(conn, matching_zones, vpc_id, vpc_region, zone_in, record):
    for z in matching_zones:
        zone_details = conn.get_hosted_zone(z)['GetHostedZoneResponse']  # could be in different regions or have different VPCids
        current_vpc_id = None
        current_vpc_region = None
        if isinstance(zone_details['VPCs'], dict):
            if zone_details['VPCs']['VPC']['VPCId'] == vpc_id:
                current_vpc_id = zone_details['VPCs']['VPC']['VPCId']
                current_vpc_region = zone_details['VPCs']['VPC']['VPCRegion']
        else:
            if vpc_id in [v['VPCId'] for v in zone_details['VPCs']]:
                current_vpc_id = vpc_id
                if vpc_region in [v['VPCRegion'] for v in zone_details['VPCs']]:
                    current_vpc_region = vpc_region
        if vpc_id == current_vpc_id and vpc_region == current_vpc_region:
            record['zone_id'] = z
            record['name'] = zone_in
            record['msg'] = "There is already a private hosted zone in the same region with the same VPC \
                you chose. Unable to create a new private hosted zone in the same name space."
            changed = False
            return changed, record

    result = conn.create_hosted_zone(zone_in, **record)
    hosted_zone = result['CreateHostedZoneResponse']['HostedZone']
    zone_id = hosted_zone['Id'].replace('/hostedzone/', '')
    record['zone_id'] = zone_id
    record['name'] = zone_in
    changed = True
    return changed, record


def create_public(conn, matching_zones, zone_in, record):
    if zone_in in matching_zones.values():
        zone_details = conn.get_hosted_zone(
            list(matching_zones)[0])['GetHostedZoneResponse']['HostedZone']
        changed = False
    else:
        result = conn.create_hosted_zone(zone_in, **record)
        zone_details = result['CreateHostedZoneResponse']['HostedZone']
        changed = True

    record['zone_id'] = zone_details['Id'].replace('/hostedzone/', '')
    record['name'] = zone_details['Name']

    return changed, record


def delete_private(conn, matching_zones, vpc_id, vpc_region):
    changed = False
    for z in matching_zones:
        zone_details = conn.get_hosted_zone(z)['GetHostedZoneResponse']
        if isinstance(zone_details['VPCs'], dict):
            if zone_details['VPCs']['VPC']['VPCId'] == vpc_id and vpc_region == zone_details['VPCs']['VPC']['VPCRegion']:
                conn.delete_hosted_zone(z)
                changed = True
                msg = "Successfully deleted %s" % matching_zones[z]
                break
            else:
                changed = False
        else:
            if vpc_id in [v['VPCId'] for v in zone_details['VPCs']] and vpc_region in [v['VPCRegion'] for v in zone_details['VPCs']]:
                conn.delete_hosted_zone(z)
                changed = True
                msg = "Successfully deleted %s" % matching_zones[z]
                break
            else:
                changed = False
    if not changed:
        msg = "The vpc_id and the vpc_region do not match a private hosted zone."

    return changed, msg


def delete_public(conn, matching_zones):
    if len(matching_zones) > 1:
        changed = False
        msg = "There are multiple zones that match. Use hosted_zone_id to specify the correct zone."
    else:
        for z in matching_zones:
            conn.delete_hosted_zone(z)
            changed = True
            msg = "Successfully deleted %s" % matching_zones[z]
    return changed, msg


def delete_hosted_id(conn, hosted_zone_id, matching_zones):
    if hosted_zone_id == "all":
        deleted = []
        for z in matching_zones:
            deleted.append(z)
            conn.delete_hosted_zone(z)
        changed = True
        msg = "Successfully deleted zones: %s" % deleted
    elif hosted_zone_id in matching_zones:
        conn.delete_hosted_zone(hosted_zone_id)
        changed = True
        msg = "Successfully deleted zone: %s" % hosted_zone_id
    else:
        changed = False
        msg = "There is no zone to delete that matches hosted_zone_id %s." % hosted_zone_id
    return changed, msg


def delete(conn, module, matching_zones):
    zone_in = module.params.get('zone').lower()
    vpc_id = module.params.get('vpc_id')
    vpc_region = module.params.get('vpc_region')
    comment = module.params.get('comment')
    hosted_zone_id = module.params.get('hosted_zone_id')

    if not zone_in.endswith('.'):
        zone_in += "."

    private_zone = bool(vpc_id and vpc_region)

    if zone_in in matching_zones.values():
        if hosted_zone_id:
            changed, result = delete_hosted_id(conn, hosted_zone_id, matching_zones)
        else:
            if private_zone:
                changed, result = delete_private(conn, matching_zones, vpc_id, vpc_region)
            else:
                changed, result = delete_public(conn, matching_zones)
    else:
        changed = False
        result = "No zone to delete."

    return changed, result


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        zone=dict(required=True),
        state=dict(default='present', choices=['present', 'absent']),
        vpc_id=dict(default=None),
        vpc_region=dict(default=None),
        comment=dict(default=''),
        hosted_zone_id=dict()))
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    zone_in = module.params.get('zone').lower()
    state = module.params.get('state').lower()
    vpc_id = module.params.get('vpc_id')
    vpc_region = module.params.get('vpc_region')

    if not zone_in.endswith('.'):
        zone_in += "."

    private_zone = bool(vpc_id and vpc_region)

    _, _, aws_connect_kwargs = get_aws_connection_info(module)

    # connect to the route53 endpoint
    try:
        conn = Route53Connection(**aws_connect_kwargs)
    except boto.exception.BotoServerError as e:
        module.fail_json(msg=e.error_message)

    zones = find_zones(conn, zone_in, private_zone)
    if state == 'present':
        changed, result = create(conn, module, matching_zones=zones)
    elif state == 'absent':
        changed, result = delete(conn, module, matching_zones=zones)

    if isinstance(result, dict):
        module.exit_json(changed=changed, result=result, **result)
    else:
        module.exit_json(changed=changed, result=result)

if __name__ == '__main__':
    main()
