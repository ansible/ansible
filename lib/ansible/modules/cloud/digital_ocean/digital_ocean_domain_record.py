#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: digital_ocean_domain_record
author: "Adam Papai (@woohgit)"
short_description: Manage DigitalOcean domain records
description:
     - Create/delete a domain record in DigitalOcean.
version_added: "2.5"
options:
  state:
    description:
     - Indicate desired state of the target.
    default: present
    choices: [ present, absent ]
  oauth_token:
    description:
     - DigitalOcean OAuth token.
    required: true
    default: None
  domain:
    description:
     - Name of the domain.
    required: true
    default: None
  type:
    description:
     - The type of record you would like to create.
    choices: [ A, AAAA, CNAME, NS, TXT, MX, SRV ]
    required: false
    default: A
  data:
    description:
     - this is the value of the record, depending on the record type.
    required: true
    default: None
  name:
    description:
     - Required for C(A, AAAA, CNAME, TXT, SRV) records. The host name, alias, or service being defined by the record.
    required: false
    default: "@"
  priority:
    description:
     - The priority of the host for C(SRV, MX) records).
    required: false
    default: None
  port:
    description:
     - The port that the service is accessible on for SRV records only.
    required: false
    default: None
  weight:
    description:
     - The weight of records with the same priority for SRV records only.
    required: false
    default: None
  ttl:
    description:
     - Time to live for the record, in seconds.
    required: false
    default: 1800
  flags:
    description:
     - An unsignedinteger between 0-255 used for CAA records.
    required: false
    default: None
  tag:
    description:
     - The parameter tag for CAA records.
    choices: [ issue, wildissue, iodef ]
    required: false
    default: None

notes:
  - Version 2 of DigitalOcean API is used.
  - The number of requests that can be made through the API is currently limited to 5,000 per hour per OAuth token.
requirements:
  - "python >= 2.6"
'''

EXAMPLES = '''
- name: Create default A record for example.com
  digital_ocean_domain_record:
    state: present
    domain: example.com
    type: A
    name: "@"
    data: 127.0.0.1

- name: Create A record for www.example.com
  digital_ocean_domain_record:
    state: present
    domain: example.com
    type: A
    name: www
    data: 127.0.0.1

- name: Remove www record
  digital_ocean_domain_record:
    state: absent
    domain: example.com
    type: A
    name: www
    data: 127.0.0.1

- name: Create MX record with priority 10 for example.com
  digital_ocean_domain_record:
    state: present
    domain: example.com
    type: MX
    data: mail1.example.com
    priority: 10
'''

RETURN = '''
id:
    description: A unique identifier for each domain record
    returned: when record is created
    type: int
    sample: 3352896
type:
    description: The type of the DNS record.
    returned: when record is created
    type: string
    sample: "CNAME"
name:
    description: The host name, alias, or service being defined by the record.
    returned: when record is created
    type: string
    sample: "www"
data:
    description: Variable data depending on record type.
    returned: when record is created
    type: string
    sample: "192.168.0.1"
priority:
    description: The priority for SRV and MX records.
    returned: when record is created
    type: int
    sample: 10
port:
    description: The port for SRV records.
    returned: when record is created
    type: int
    sample: 5556
ttl:
    description: This value is the time to live for the record, in seconds.
    returned: when record is created
    type: int
    sample: 3600
weight:
    description: The weight for SRV records.
    returned: when record is created
    type: int
    sample: 50
flags:
    description: An unsigned integer between 0-255 used for CAA records.
    returned: when record is created
    type: int
    sample: 16
tag:
    description: The parameter tag for CAA records.
    returned: when record is created
    type: string
    sample: "issue"
'''

from ansible.module_utils.basic import env_fallback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper


def verify_domain(module, rest, domain):
    # URL https://api.digitalocean.com/v2/domains/[NAME]
    response = rest.get('domains/%s' % domain)
    status_code = response.status_code
    json = response.json

    if status_code not in (200, 404):
        module.fail_json(msg='Error getting domain [%(status_code)s: %(json)s]' % {'status_code': status_code, 'json': json})
    elif status_code == 404:
        module.fail_json(msg="No domain named '%s' found. Please create a domain first" % domain)


def get_all_records(module, rest):
    domain = module.params.get('domain').lower()

    records = []
    page = 1
    while True:
        # GET /v2/domains/$DOMAIN_NAME/records
        response = rest.get('domains/%(domain)s/records?page=%(page)s' % {'domain': domain, 'page': page})
        status_code = response.status_code
        json = response.json

        if status_code != 200:
            module.fail_json(msg='Error getting domain records [%(status_code)s: %(json)s]' % {'status_code': status_code, 'json': json})

        for record in json['domain_records']:
            records.append(dict([(str(k), v) for k, v in record.items()]))

        if 'pages' in json['links'] and 'next' in json['links']['pages']:
            page += 1
        else:
            break

    return records


def normalize_data(payload):
    # for the MX, CNAME, SRV, CAA records make sure the data ends with a dot
    if (payload['type'] in ['CNAME', 'MX', 'SRV', 'CAA'] and payload['data'] != '@' and not payload['data'].endswith(".")):
        data = "%s." % payload['data']
    else:
        data = payload['data']

    return data


def get_matching_record(module, rest):
    records = get_all_records(module, rest)
    payload = build_payload(module)

    # look for exactly the same record
    if records:
        for record in records:
            record_id = record['id']
            del record['id']
            # python3 does not have cmp so let's use the official workaround
            if (record > payload) - (record < payload) == 0:
                return record, record_id

    return None, None


def create_record(module, rest, domain):
    payload = build_payload(module)
    record, _ = get_matching_record(module, rest)

    if record is None:
        payload['data'] = normalize_data(payload)

        # POST /v2/domains/$DOMAIN_NAME/records
        response = rest.post('domains/%s/records' % domain, data=payload)
        status_code = response.status_code
        json = response.json
        if status_code == 201:
            changed = True
            return changed, json['domain_record']
        else:
            module.fail_json(msg='Error creating domain record [%(status_code)s: %(json)s]' % {'status_code': status_code, 'json': json})
    else:
        changed = False
        result = "Record has been already created"
        return changed, result


def build_payload(module):
    domain = module.params.get('domain').lower()

    payload = dict(
        data=module.params.get('data'),
        flags=module.params.get('flags'),
        name=module.params.get('name'),
        port=module.params.get('port'),
        priority=module.params.get('priority'),
        type=module.params.get('type').upper(),
        tag=module.params.get('tag'),
        ttl=module.params.get('ttl'),
        weight=module.params.get('weight')
    )

    # DigitalOcean stores every data in lowercase except TXT
    if payload['type'] != 'TXT':
        payload['data'] = payload['data'].lower()

    # digitalocean stores data: '@' if the data=domain
    if payload['data'] == domain:
        payload['data'] = '@'

    return payload


def delete_record(module, rest, domain):
    record, record_id = get_matching_record(module, rest)

    if record is None:
        changed = False
        return changed, record
    else:
        # DELETE /v2/domains/$DOMAIN_NAME/records/$RECORD_ID.
        response = rest.delete('domains/%(domain)s/records/%(id)s' % {'domain': domain, 'id': record_id})
        status_code = response.status_code
        json = response.json
        if status_code == 204:
            changed = True
            msg = "Successfully deleted %s" % record['name']
            return changed, msg
        else:
            module.fail_json(msg="Error deleting domain record. [%(status_code)s: %(json)s]" % {'status_code': status_code, 'json': json})


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['present', 'absent'], default='present'),
            oauth_token=dict(
                no_log=True,
                fallback=(env_fallback, ['DO_API_TOKEN', 'DO_API_KEY', 'DO_OAUTH_TOKEN']),
                required=True,
            ),
            domain=dict(type='str', required=True),
            type=dict(choices=['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'SRV', 'NS', 'CAA'], required=True),
            name=dict(type='str', default='@'),
            data=dict(type='str', required=True),
            priority=dict(type='int'),
            port=dict(type='int'),
            weight=dict(type='int'),
            ttl=dict(type='int', default=1800),
            tag=dict(choices=['issue', 'wildissue', 'iodef'], required=False),
            flags=dict(type='int', required=False),
        )
    )

    rest = DigitalOceanHelper(module)

    # Check if oauth_token is valid or not
    response = rest.get('account')
    if response.status_code == 401:
        module.fail_json(msg='Failed to login using oauth_token, please verify validity of oauth_token')

    state = module.params.get('state')
    domain = module.params.get('domain').lower()

    verify_domain(module, rest, domain)

    if state == 'present':
        changed, result = create_record(module, rest, domain)
    elif state == 'absent':
        changed, result = delete_record(module, rest, domain)

    module.exit_json(changed=changed, result=result)


if __name__ == '__main__':
    main()
