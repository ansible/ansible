#!/usr/bin/python

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ovh_dns
author: Albin Kerouanton @NiR-
short_description: Manage OVH DNS records
description:
    - Manage OVH (French European hosting provider) DNS records
version_added: "2.6"
notes:
    - Uses the python OVH Api U(https://github.com/ovh/python-ovh).
      You have to create an application (a key and secret) with a consummer
      key as described into U(https://eu.api.ovh.com/g934.first_step_with_api).
    - Your domains should be configured to use OVH DNS servers. This module
      won't configure them, so you have to go on OVH UI and change DNS servers
      for appropriate domains.
requirements: [ "ovh" ]
options:
    domain:
        required: true
        description:
            - Name of the domain zone
    subdomain:
        default: ""
        required: false
        description:
            - >
              Subdomain of the DNS record. It has to be relative to your domain.
              Leaving subdomain empty or unspecified will affect the domain
              itself.
    target:
        required: true
        description:
            - Target of the DNS record.
    type:
        default: A
        choices: ['A', 'AAAA', 'CNAME', 'DKIM', 'LOC', 'MX', 'NAPTR', 'PTR', 'SPF', 'SRV', 'SSHFP']
        description:
            - Type of DNS record (A, AAAA, PTR, CNAME, etc.)
    ttl:
        default: 0
        description:
            - Time to live associated to the DNS record. It's not mandatory
              when deleting records therefore you could use default value 0,
              but otherwise you shall pass a value. Also note that OVH does
              not accept too low TTL values (< 60 seconds).
    state:
        default: present
        choices: ['present', 'absent']
        description:
            - Determines wether the record is to be created/modified or deleted
    endpoint:
        required: true
        description:
            - The endpoint to use ( for instance ovh-eu)
    application_key:
        required: true
        description:
            - The applicationKey to use
    application_secret:
        required: true
        description:
            - The application secret to use
    consumer_key:
        required: true
        description:
            - The consumer key to use
'''

EXAMPLES = '''
# Create an A record for "mydomain.com", pointing to 1.2.3.4
- ovh_dns:
    state: present
    domain: mydomain.com
    type: A
    target: 1.2.3.4
    ttl: 3600
    endpoint: ovh-eu
    application_key: yourkey
    application_secret: yoursecret
    consumer_key: yourconsumerkey

# Create a A record for subdomain "api.staging.mydomain.com", pointing to 1.2.3.4
- ovh_dns:
    state: present
    domain: mydomain.com
    subdomain: db1.staging
    target: 1.2.3.4
    ttl: 3600
    endpoint: ovh-eu
    application_key: yourkey
    application_secret: yoursecret
    consumer_key: yourconsumerkey

# Create a CNAME record "www" pointing to "cdn"
- ovh_dns:
    state: present
    domain: mydomain.com
    subdomain: www
    type: CNAME
    target: cdn
    ttl: 3600
    endpoint: ovh-eu
    application_key: yourkey
    application_secret: yoursecret
    consumer_key: yourconsumerkey

# Delete an existing record, must specify all parameters (TTL can be omitted)
- ovh_dns:
    state: absent
    domain: mydomain.com
    subdomain: www
    type: CNAME
    target: cdn
    endpoint: ovh-eu
    application_key: yourkey
    application_secret: yoursecret
    consumer_key: yourconsumerkey
'''

RETURN = '''
'''

import os
import sys

try:
    import ovh
    from ovh.exceptions import APIError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False

from ansible.module_utils.basic import AnsibleModule


def get_ovh_client(module):
    endpoint = module.params.get('endpoint')
    application_key = module.params.get('application_key')
    application_secret = module.params.get('application_secret')
    consumer_key = module.params.get('consumer_key')

    return ovh.Client(
        endpoint=endpoint,
        application_key=application_key,
        application_secret=application_secret,
        consumer_key=consumer_key
    )


def get_domain_records(client, domain):
    """Obtain all records for a specific domain"""
    records = {}

    # List all ids and then get info for each one
    record_ids = client.get('/domain/zone/{0}/record'.format(domain))

    for record_id in record_ids:
        info = client.get('/domain/zone/{0}/record/{1}'.format(domain, record_id))
        add_record(records, info)

    return records


def add_record(records, info):
    fieldtype = info['fieldType']
    subdomain = info['subDomain']
    targetval = info['target']

    if fieldtype not in records:
        records[fieldtype] = dict()
    if subdomain not in records[fieldtype]:
        records[fieldtype][subdomain] = dict()

    records[fieldtype][subdomain][targetval] = info


def find_record(records, subdomain, fieldtype, targetval):
    if fieldtype not in records:
        return False
    if subdomain not in records[fieldtype]:
        return False
    if targetval not in records[fieldtype][subdomain]:
        return False

    return records[fieldtype][subdomain][targetval]


def ensure_record_present(module, records, client):
    domain = module.params.get('domain')
    subdomain = module.params.get('subdomain')
    fieldtype = module.params.get('type')
    targetval = module.params.get('target')
    ttl = int(module.params.get('ttl'))
    record = find_record(records, subdomain, fieldtype, targetval)

    # Does the record exist already?
    if record:
        # The record is already as requested, no need to change anything
        if ttl == record['ttl']:
            module.exit_json(changed=False)

        if module.check_mode:
            module.exit_json(changed=True, diff=dict(ttl=ttl))

        try:
            # find_record is based on record subdomain, field type
            # and target there's only ttl property left to be updated
            client.put('/domain/zone/{0}/record/{1}'.format(domain, record['id']), ttl=ttl)
        except APIError as error:
            module.fail_json(
                msg='Unable to call OVH api for updating the record "{0} {1} {2}" with ttl {3}. '
                    'Error returned by OVH api is: "{4}".'.format(subdomain, fieldtype, targetval, ttl, error))

        refresh_domain(module, client, domain)
        module.exit_json(changed=True)

    if module.check_mode:
        module.exit_json(changed=True, diff=dict(subdomain=subdomain, type=fieldtype, target=targetval, ttl=ttl))

    try:
        # Add the record
        client.post('/domain/zone/{0}/record'.format(domain),
                    fieldType=fieldtype,
                    subDomain=subdomain,
                    target=targetval,
                    ttl=ttl)
    except APIError as error:
        module.fail_json(msg='Unable to call OVH api for adding the record "{0} {1} {2}". '
                             'Error returned by OVH api is: "{3}".'.format(subdomain, fieldtype, targetval, error))

    refresh_domain(module, client, domain)
    module.exit_json(changed=True)


def refresh_domain(module, client, domain):
    try:
        client.post('/domain/zone/{0}/refresh'.format(domain))
    except APIError as error:
        module.fail_json(
            msg='Unable to call OVH api to refresh domain "{0}". '
                'Error returned by OVH api is: "{1}"'.format(domain, error))


def ensure_record_absent(module, records, client):
    domain = module.params.get('domain')
    subdomain = module.params.get('subdomain')
    fieldtype = module.params.get('type')
    targetval = module.params.get('target')
    record = find_record(records, subdomain, fieldtype, targetval)

    if not record:
        module.exit_json(changed=False)

    if module.check_mode:
        module.exit_json(changed=True)

    try:
        # Remove the record
        client.delete('/domain/zone/{0}/record/{1}'.format(domain, record['id']))
    except APIError as error:
        module.fail_json(
            msg='Unable to call OVH api for deleting the record "{0}" for "{1}"". '
                'Error returned by OVH api is: "{2}".'.format(subdomain, domain, error))

    refresh_domain(module, client, domain)
    module.exit_json(changed=True)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            domain=dict(required=True),
            subdomain=dict(default=''),
            target=dict(required=True),
            type=dict(default='A', choices=['A', 'AAAA', 'CNAME', 'DKIM', 'LOC', 'MX', 'NAPTR', 'PTR', 'SPF', 'SRV', 'SSHFP']),
            ttl=dict(type='int', default=0),
            state=dict(default='present', choices=['present', 'absent']),
            endpoint=dict(required=True),
            application_key=dict(required=True, no_log=True),
            application_secret=dict(required=True, no_log=True),
            consumer_key=dict(required=True, no_log=True)
        ),
        supports_check_mode=True
    )

    if not HAS_OVH:
        module.fail_json(msg='ovh python module is required to run this module.')

    # Get parameters
    domain = module.params.get('domain')
    subdomain = module.params.get('subdomain')
    state = module.params.get('state')

    # Connect to OVH API
    client = get_ovh_client(module)

    try:
        # Check that the domain exists
        domains = client.get('/domain/zone')
    except APIError as error:
        module.fail_json(
            msg='Unable to call OVH api for getting the list of domains. '
                'Check application key, secret, consumer key & parameters. '
                'Error returned by OVH api is: "{0}".'.format(error))

    if domain not in domains:
        module.fail_json(msg='Domain {0} does not exist'.format(domain))

    try:
        # Obtain all domain records to check status against what is demanded
        records = get_domain_records(client, domain)
    except APIError as error:
        module.fail_json(
            msg='Unable to call OVH api for getting the list of records for "{0}". '
                'Error returned by OVH api is: "{1}".'.format(domain, error))

    if state == 'absent':
        ensure_record_absent(module, records, client)
    elif state == 'present':
        ensure_record_present(module, records, client)

    # We should never reach here
    module.fail_json(msg='Internal ovh_dns module error')


if __name__ == '__main__':
    main()
