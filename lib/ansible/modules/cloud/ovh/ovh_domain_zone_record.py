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
module: ovh_domain_zone_record
short_description: Manage OVH domain zone records
description:
    - Manage OVH (French European hosting provider) domain zone records.
version_added: "2.8"
author: Loïc Latreille (@psykotox)
notes:
    - Uses the python OVH Api U(https://github.com/ovh/python-ovh).
      You have to create an application (a key and secret) with a consummer
      key as described into U(https://eu.api.ovh.com/g934.first_step_with_api)
requirements:
    - ovh >  0.3.5
options:
    name:
        required: true
        description:
            - Name of the domain zone.
    subdomain:
        description:
            - The subdomain of the record to manage.
    targets:
        required: true
        description:
            - Targets list of the record to manage.
    ttl:
        required: false
        description:
            - The TTL of the record to manage.
    state:
        default: present
        choices: ['present', 'absent']
        description:
            - Determines whether the record is to be created/modified
              or deleted.
    record_type:
        required: true
        choices: ['A', 'AAAA', 'CAA' , 'CNAME', 'DKIM', 'LOC', 'MX',
                  'NAPTR', 'NS', 'PTR', 'SPF', 'SRV', 'SSHFP', 'TLSA',
                  'TXT']
        description:
            - Determines the type of record to use.
    endpoint:
        required: true
        description:
            - The endpoint to use (for instance ovh-eu).
    application_key:
        required: true
        description:
            - The application key to use.
    application_secret:
        required: true
        description:
            - The application secret to use.
    consumer_key:
        required: true
        description:
            - The consumer key to use.

'''

EXAMPLES = '''
# Adds or modify the record MX of the zone example.com with
# targets 1.1.1.1 and 2.2.2.2
- ovh_domain_zone_record:
    name: example.com
    record_type: MX
    state: present
    targets:
        - 1.1.1.1
        - 2.2.2.2
    endpoint: ovh-eu
    application_key: yourkey
    application_secret: yoursecret
    consumer_key: yourconsumerkey

# Removes the record A of the subdomain test
# of the zone example.com with the target 1.1.1.1
- ovh_domain_zone_record:
    name: example.com
    subdomain: test
    record_type: A
    state: absent
    targets: 1.1.1.1
    endpoint: ovh-eu
    application_key: yourkey
    application_secret: yoursecret
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule
try:
    from ovh.exceptions import APIError, ResourceNotFoundError
except ImportError:
    pass
from ansible.module_utils.ovh_api import ovh_argument_spec, ovh_connect_to_api


def main():
    argument_spec = ovh_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        subdomain=dict(required=False, default=''),
        targets=dict(required=True, type='list'),
        record_type=dict(required=True, choices=['A', 'AAAA', 'CAA', 'CNAME',
                                                 'DKIM', 'LOC', 'MX', 'NAPTR',
                                                 'NS', 'PTR', 'SPF', 'SRV',
                                                 'SSHFP', 'TLSA', 'TXT']),
        ttl=dict(required=False, type='int', default=0),
        state=dict(default='present', choices=['present', 'absent'])
    ))

    module = AnsibleModule(argument_spec=argument_spec)

    # Get parameters
    name = module.params.get('name')
    state = module.params.get('state')
    subdomain = module.params.get('subdomain')
    targets = module.params.get('targets')
    record_type = module.params.get('record_type')
    ttl = module.params.get('ttl')

    # Connect to OVH API
    ovhApi = ovh_connect_to_api(module)

    try:
        records = ovhApi.get('/domain/zone/{0}/record'.format(name), fieldType=record_type, subDomain=subdomain)
    except ResourceNotFoundError as notFoundError:
        module.fail_json(
            msg='Domain zone {0} does not exist. Error returned by OVH api was : {1}'
                .format(name, notFoundError))
    except APIError as apiError:
        module.fail_json(
            msg='Unable to call OVH api for getting the list of records '
                'of the domain zone. Error returned by OVH api was : {0}'
                .format(apiError))

    recordProperties = []
    newTargets = list(targets)
    for record in records:
        try:
            recordProperty = ovhApi.get('/domain/zone/{0}/record/{1}'.format(name, record))
        except APIError as apiError:
            module.fail_json(
                msg='Unable to call OVH api for getting the property of a record '
                    'of the domain zone. Error returned by OVH api was : {0}'
                    .format(apiError))
        recordProperties.append(recordProperty)
        if recordProperty['target'] in newTargets:
            newTargets.remove(recordProperty['target'])

    moduleChanged = False
    for recordProperty in recordProperties:
        if recordProperty['target'] in targets:
            if state == "absent":
                # Delete record
                try:
                    ovhApi.delete('/domain/zone/{0}/record/{1}'.format(name, recordProperty['id']))
                except APIError as apiError:
                    module.fail_json(
                        msg='Unable to call OVH api for deleting the record. '
                            'Error returned by OVH api was : {0}'.format(apiError))
                moduleChanged = True
            else:
                if recordProperty['ttl'] != ttl:
                    # Update ttl
                    try:
                        ovhApi.put(
                            '/domain/zone/{0}/record/{1}'
                            .format(name, recordProperty['id']), ttl=ttl)
                    except APIError as apiError:
                        module.fail_json(
                            msg='Unable to call OVH api for updating the ttl of the '
                                'record. Error returned by OVH api was : {0}'
                                .format(apiError))
                    moduleChanged = True
        else:
            if state == "present":
                # Delete record (target change)
                try:
                    ovhApi.delete('/domain/zone/{0}/record/{1}'.format(name, recordProperty['id']))
                except APIError as apiError:
                    module.fail_json(
                        msg='Unable to call OVH api for deleting the record. '
                            'Error returned by OVH api was : {0}'.format(apiError))
                moduleChanged = True

    for newTarget in newTargets:
        if state == "present":
            # Add record
            try:
                ovhApi.post(
                    '/domain/zone/{0}/record'.format(name), fieldType=record_type,
                    subDomain=subdomain, target=newTarget, ttl=ttl)
            except APIError as apiError:
                module.fail_json(
                    msg='Unable to call OVH api for adding the record, '
                        'Error returned by OVH api was : {0}'.format(apiError))
            moduleChanged = True

    if moduleChanged:
        # Apply zone modification
        try:
            ovhApi.post('/domain/zone/{0}/refresh'.format(name))
        except APIError as apiError:
                module.fail_json(
                    msg='Unable to call OVH api for refreshing the domain zone, '
                        'Error returned by OVH api was : {0}'.format(apiError))

    module.exit_json(changed=moduleChanged)


if __name__ == '__main__':
    main()
