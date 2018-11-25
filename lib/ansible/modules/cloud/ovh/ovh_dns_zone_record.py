#!/usr/bin/python

# Copyright: (c) 2018, Hedi Chaibi <contact@hedichaibi.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ovh_dns_zone_record
short_description: Manage OVH DNS records
version_added: "2.8"
description:
    - Create, delete or update OVH DNS zone records
options:
    name:
        description:
            - The DNS record name (subdomain)
    zone_name:
        description:
            - The name of the domain zone
        required: true
    target:
        description:
            - The DNS record target
    type:
        description:
            - The DNS record type
        default: A
        choices: ["A", "AAAA", "CAA", "CNAME", "DKIM", "DMARC", "LOC", "MX", "NAPTR", "NS", "PTR", "SPF", "SRV", "SSHFP", "TLSA", "TXT"]
    ttl:
        description:
            - The DNS record Time To Live
        type: int
        default: 0
    state:
        description:
            - Whether the DNS record should exist
        default: present
        choices: ["present", "absent"]
    endpoint:
        description:
            - The ovh api endpoint
        required: true
        choices: ["ovh-eu", "ovh-us", "ovh-ca"]
    application_key:
        description:
            - The ovh api application key
        required: true
    application_secret:
        description:
            - The ovh api application secret
        required: true
    consumer_key:
        description:
            - The ovh api application consumer key
        required: true
author:
    - Hedi Chaibi (@hedii)
notes:
    - Uses the python OVH Api U(https://github.com/ovh/python-ovh). You have to
      create an application (a key and secret) with a consumer key as described
      into U(https://docs.ovh.com/gb/en/customer/first-steps-with-ovh-api/)
requirements:
    - ovh >  0.3.5
'''

EXAMPLES = '''
# Create an A record for domain foo.example.com with a ttl of 0 pointing to
# 111.222.333.444
- ovh_dns_zone_record:
    name: foo
    zone_name: example.com
    target: 111.222.333.444
    endpoint: ovh-eu
    application_key: yourkey
    application_secret: yoursecret
    consumer_key: yourconsumerkey

# Delete a CNAME record for domain bar.example.com
- ovh_dns_zone_record:
    name: bar
    zone_name: example.com
    type: CNAME
    state: absent
    endpoint: ovh-eu
    application_key: yourkey
    application_secret: yoursecret
    consumer_key: yourconsumerkey

# Create an CNAME record for domain foo.example.com with a ttl of 0 pointing to
# example.com
- ovh_dns_zone_record:
    name: foo
    zone_name: example.com
    target: example.com.
    endpoint: ovh-eu
    application_key: yourkey
    application_secret: yoursecret
    consumer_key: yourconsumerkey

# Create a AAAA record for domain baz.example.com with a ttl of 86400 seconds
# pointing to 2001:0db8:0000:85a3:0000:0000:ac1f:8001
- ovh_dns_zone_record:
    name: baz
    zone_name: example.com
    target: 2001:0db8:0000:85a3:0000:0000:ac1f:8001
    type: AAAA
    ttl: 86400
    state: present
    endpoint: ovh-eu
    application_key: yourkey
    application_secret: yoursecret
    consumer_key: yourconsumerkey
'''

RETURN = '''
id:
    description: dns zone record id
    returned: when dns zone record exists
    type: int
    sample: 1471529024
name:
    description: dns zone record name
    returned: when dns zone record exists
    type: str
    sample: "docs"
zone_name:
    description: dns zone name
    returned: when dns zone record exists
    type: str
    sample: "ansible.com"
target:
    description: dns zone record target
    returned: when dns zone record exists
    type: str
    sample: "104.24.17.59"
type:
    description: dns zone record type
    returned: when dns zone record exists
    type: str
    sample: "A"
ttl:
    description: dns zone record ttl
    returned: when dns zone record exists
    type: int
    sample: 86400
'''

try:
    from ovh import Client, APIError, ResourceNotFoundError

    HAS_OVH = True
except ImportError:
    HAS_OVH = False

from ansible.module_utils.basic import AnsibleModule


def get_api_client(module):
    return Client(
        endpoint=module.params.get('endpoint'),
        application_key=module.params.get('application_key'),
        application_secret=module.params.get('application_secret'),
        consumer_key=module.params.get('consumer_key')
    )


def get_zone_records(module, client, zone_name):
    try:
        records = []
        for record_id in client.get('/domain/zone/{0}/record'.format(zone_name)):
            records.append(get_zone_record(module, client, zone_name, record_id))
        return records
    except ResourceNotFoundError as error:
        module.fail_json(msg='DNS zone {0} not found. OVH api error: {1}'.format(zone_name, error))
    except APIError as error:
        module.fail_json(msg='OVH api error while getting zone records: {0}'.format(error))


def get_zone_record(module, client, zone_name, record_id):
    try:
        return client.get('/domain/zone/{0}/record/{1}'.format(zone_name, record_id))
    except APIError as error:
        module.fail_json(msg='OVH api error while getting zone record: {0}'.format(error))


def create_zone_record(module, client, zone_name, name, target, record_type, ttl):
    try:
        if not module.check_mode:
            record = client.post('/domain/zone/{0}/record'.format(zone_name),
                                 subDomain=name,
                                 target=target,
                                 fieldType=record_type,
                                 ttl=ttl)
            data = dict(record=get_zone_record(module, client, zone_name, record['id']))
        else:
            data = dict()
        return refresh_zone(module, client, zone_name, data)
    except APIError as error:
        module.fail_json(msg='OVH api error while creating zone record: {0}'.format(error))


def update_zone_record(module, client, zone_name, record_id, name, target, ttl):
    try:
        if not module.check_mode:
            client.put('/domain/zone/{0}/record/{1}'.format(zone_name, record_id),
                       subDomain=name,
                       target=target,
                       ttl=ttl)
        data = dict(record=get_zone_record(module, client, zone_name, record_id))
        return refresh_zone(module, client, zone_name, data)
    except APIError as error:
        module.fail_json(msg='OVH api error while updating zone record: {0}'.format(error))


def delete_zone_record(module, client, zone_name, record_id):
    try:
        if not module.check_mode:
            client.delete('/domain/zone/{0}/record/{1}'.format(zone_name, record_id))
        return refresh_zone(module, client, zone_name, data=dict())
    except APIError as error:
        module.fail_json(msg='OVH api error while deleting zone record: {0}'.format(error))


def refresh_zone(module, client, zone_name, data):
    try:
        if not module.check_mode:
            client.post('/domain/zone/{0}/refresh'.format(zone_name))

        if 'record' in data:
            data['record'] = api_record_to_result_zone(data['record'])

        return data
    except APIError as error:
        module.fail_json(msg='OVH api error while refreshing zone: {0}'.format(error))


def record_exists(record, expected_field_type, expected_record_name):
    return record['fieldType'] == expected_field_type and record['subDomain'] == expected_record_name


def api_record_to_result_zone(record):
    return dict(
        id=record['id'],
        name=record['subDomain'],
        zone_name=record['zone'],
        target=record['target'],
        type=record['fieldType'],
        ttl=record['ttl'],
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', default=''),
            zone_name=dict(type='str', required=True),
            target=dict(type='str'),
            type=dict(type='str',
                      choices=['A', 'AAAA', 'CAA', 'CNAME', 'DKIM', 'DMARC', 'LOC', 'MX', 'NAPTR', 'NS', 'PTR', 'SPF',
                               'SRV', 'SSHFP', 'TLSA', 'TXT'], default='A'),
            ttl=dict(type='int', default=0),
            state=dict(type='str', choices=['present', 'absent'], default='present'),
            endpoint=dict(required=True, choices=['ovh-eu', 'ovh-us', 'ovh-ca']),
            application_key=dict(required=True, no_log=True),
            application_secret=dict(required=True, no_log=True),
            consumer_key=dict(required=True, no_log=True)
        ),
        supports_check_mode=True
    )

    if not HAS_OVH:
        module.fail_json(msg='ovh python module is required to run this module.')

    record_name = module.params.get('name')
    zone_name = module.params.get('zone_name')
    target = module.params.get('target')
    record_type = module.params.get('type')
    ttl = module.params.get('ttl')
    state = module.params.get('state')

    client = get_api_client(module)

    records = get_zone_records(module, client, zone_name)

    if state == 'present':
        if target == '' or target is None:
            module.fail_json(msg='target is required if state is present')

        record_id = False
        for record in records:
            if record_exists(record, expected_field_type=record_type, expected_record_name=record_name):
                if record['target'] == target and record['ttl'] == ttl:
                    # nothing to change, we exit
                    data = dict(record=api_record_to_result_zone(record))
                    module.exit_json(changed=False, **data)
                else:
                    record_id = record['id']
        if record_id:
            # a record matches, we need to update
            data = update_zone_record(module, client, zone_name=zone_name, record_id=record_id, name=record_name,
                                      target=target, ttl=ttl)
            module.exit_json(changed=True, **data)
        else:
            # no record matches, we need to create
            data = create_zone_record(module, client, zone_name=zone_name, name=record_name, target=target,
                                      record_type=record_type, ttl=ttl)
            module.exit_json(changed=True, **data)
    elif state == 'absent':
        record_id = False
        for record in records:
            if record_exists(record, expected_field_type=record_type, expected_record_name=record_name):
                record_id = record['id']
        if record_id:
            # a record matches, we need to delete
            data = delete_zone_record(module, client, zone_name, record_id)
            module.exit_json(changed=True, **data)
        else:
            # the record does not exist, nothing to change, we exit
            module.exit_json(changed=False)


if __name__ == '__main__':
    main()
