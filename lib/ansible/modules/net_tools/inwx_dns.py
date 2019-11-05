#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Nick Ufer <nu@inwx.de>
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
module: inwx_dns
author:
    - Nick Ufer (@NickUfer)
requirements:
  - python >= 2.6
  - inwx-domrobot >= 3.0.2
version_added: "2.10"
short_description: Manage INWX DNS records
notes:
    - "This module does NOT support two factor authentication due to excessive rebuilding of the API client and one time use of an OTP."
description:
    - "Manages DNS records via the INWX API."
options:
    algorithm:
        description:
            - Algorithm number.
            - Required for C(type=SSHFP) when C(state=present).
        type: int
        required: false
    flag:
        description:
            - Flag for C(type=CAA) record defining if record is critical.
            - Flag for C(type=NAPTR) record defining the returned record type.
            - Required for C(type=CAA) and C(type=NAPTR) when C(state=present).
        type: str
        required: false
    tag:
        description:
            - Tag identifier.
            - An ASCII string that defines the identifier of the property represented by the record.
            - Required for C(type=CAA) when C(state=present).
        type: str
        choices: [ issue, issuewild, iodef ]
        required: false
    cert_usage:
        description:
            - Certificate usage number.
            - Required for C(type=TLSA) when C(state=present).
        type: int
        choices: [ 0, 1, 2, 3 ]
        required: false
    domain:
        description:
            - The name of the Domain to work with (e.g. "example.com").
        type: str
        required: true
    hash_type:
        description:
            - Hash type number.
            - Required for C(type=SSHFP) and C(type=TLSA) when C(state=present).
        type: int
        required: false
    regex:
        description:
            - Regex string.
            - Defines what should be replaced with the defined C(substitution).
            - Required for C(type=NAPTR) when C(state=present).
        type: str
        required: false
    password:
        description:
            - INWX Account Password
            - Required for API authentication.
        type: str
        required: true
        aliases: [ pass ]
    priority:
        description:
            - Record priority.
            - Required for C(type=MX) and C(type=SRV)
        type: int
        required: false
        default: 1
    port:
        description:
            - Service port.
            - Required for C(type=SRV).
        type: int
        required: false
    record:
        description:
            - Record to add.
            - Required if C(state=present).
        type: str
        required: false
        default: ''
        aliases: [ name ]
    selector:
        description:
            - Selector number.
            - Required for C(type=TLSA) when C(state=present).
        type: int
        required: false
        choices: [ 0, 1 ]
    service:
        description:
            - Record service.
            - Required for C(type=SRV).
        type: str
        required: false
    state:
        description:
            - Whether the record(s) should exist or not.
        type: str
        required: true
        choices: [ absent, present ]
        default: present
    substitution:
        description:
            - Substitution string.
            - Replaces everything matching in C(regex) with the defined substitution.
            - Required for C(type=NAPTR) when C(state=present).
        type: str
        required: false
    ttl:
        description:
            - The TTL to give the new record.
            - Must be between 3600 and 2,147,483,647 seconds.
        type: int
        required: false
        default: 86400
    type:
        description:
            - The type of DNS record.
        type: str
        required: false
        choices: [ A, AAAA, AFSDB, CAA, CNAME, HINFO, LOC, MX, NAPTR, NS, PTR, RP, SOA, SRV, SSHFP, TLSA, TXT ]
    username:
        description:
            - INWX Account Username
            - Required for API authentication.
        type: str
        required: true
        aliases: [ user ]
    value:
        description:
            - The record value.
            - Required for C(state=present).
        type: str
        required: false
        aliases: [ content ]
    weight:
        description:
            - Service weight.
            - Required for C(type=SRV) and C(type=NAPTR).
        type: int
        required: false
        default: 1
'''

EXAMPLES = '''
- name: Create an A record
  inwx_dns:
    domain: example.com
    type: A
    record: test
    value: 127.0.0.1
    username: test_user
    password: test_password

- name: Delete the A record
  inwx_dns:
    domain: example.com
    type: A
    record: test
    username: test_user
    password: test_password
    state: absent

- name: Create an example.com A record with value 127.0.0.1
  inwx_dns:
    domain: example.com
    type: A
    value: 127.0.0.1
    username: test_user
    password: test_password

- name: Create another example.com A record with value 127.0.0.2 with custom ttl
  inwx_dns:
    domain: example.com
    type: A
    value: 127.0.0.2
    ttl: 43200
    username: test_user
    password: test_password

- name: Update ttl of example.com A record with value 127.0.0.1
  inwx_dns:
    domain: example.com
    type: A
    value: 127.0.0.1
    ttl: 604800
    username: test_user
    password: test_password

- name: Create an test.example.com AAAA record
  inwx_dns:
    domain: example.com
    type: AAAA
    record: test
    value: ::1
    username: test_user
    password: test_password

- name: Create an test.example.com AFSDB record
  inwx_dns:
    domain: example.com
    type: AFSDB
    record: test
    service: '1'
    value: database1.example.com
    username: test_user
    password: test_password

- name: Create a mail.example.com CNAME record
  inwx_dns:
    domain: example.com
    type: CNAME
    record: mail
    value: example.com
    username: test_user
    password: test_password

- name: Create a test.example.com CAA record
  inwx_dns:
    domain: example.com
    type: CAA
    record: test
    flag: '0'
    tag: issue
    value: ;
    username: test_user
    password: test_password

- name: Create a test.example.com HINFO record
  inwx_dns:
    domain: example.com
    type: HINFO
    record: test
    value: 'INTEL-IPSC UNIX'
    username: test_user
    password: test_password

- name: Create a test.example.com LOC record
  inwx_dns:
    domain: example.com
    type: LOC
    record: test
    value: '51 30 12.748 N 0 7 39.612 W 0.00'
    username: test_user
    password: test_password

- name: Create a mail.example.com MX record
  inwx_dns:
    domain: example.com
    type: MX
    record: mail
    priority: 1
    value: 'mail.example.com'
    username: test_user
    password: test_password

- name: Create a test.example.com NAPTR record
  inwx_dns:
    domain: example.com
    type: NAPTR
    record: test
    weight: 1
    flag: '10'
    service: 'S'
    regex: 'SIP+D2U'
    substitution: '!^.*$!sip:customer-service@example.com!'
    username: test_user
    password: test_password

- name: Create a example.com NS record
  inwx_dns:
    domain: example.com
    type: NS
    value: 'ns1.exampleserver.net'
    ttl: 86400
    username: test_user
    password: test_password

- name: Create a example.com RP record
  inwx_dns:
    domain: example.com
    type: RP
    value: mail@example.com
    username: test_user
    password: test_password

- name: Update example.com's SOA record value and ttl
  inwx_dns:
    domain: '{{ domain }}'
    type: SOA
    value: 'ns.ote.inwx.de hostmaster@inwx.de 2019103186'
    ttl: 86400
    username: '{{ username }}'
    password: '{{ password }}'

- name: Create a example.com SRV record
  inwx_dns:
    domain: example.com
    type: SRV
    record: _foo._tcp.fooservice
    value: example.com
    port: 3500
    priority: 10
    weight: 10
    username: test_user
    password: test_password

- name: Create a test.example.com SSHFP record
  inwx_dns:
    domain: example.com
    type: SSHFP
    record: test
    algorithm: '4'
    hash_type: '2'
    value: 9dc1d6742696d2f51ca1f1a78b3d16a840f7d111eb9454239e70db31363f33e1
    username: test_user
    password: test_password

- name: Create a TLSA record _25._tcp.mail.example.com
  inwx_dns:
    domain: example.com
    type: TLSA
    record: _25._tcp.mail
    cert_usage: 3
    selector: 1
    hash_type: 1
    value: 6b76d034492b493e15a7376fccd08e63befdad0edab8e442562f532338364bf3
    username: test_user
    password: test_password

- name: Create a test.example.com TXT record
  inwx_dns:
    domain: example.com
    type: TXT
    record: test
    value: 'hello world'
    username: test_user
    password: test_password
'''

RETURN = '''
record:
    description: A dictionary containing the record data.
    returned: success, except on record deletion
    type: complex
    contains:
        id:
            description: The record ID.
            returned: success
            type: int
            sample: 33121
        type:
            description: The record type.
            returned: success
            type: str
            sample: A
        name:
            description: The record name as FQDN.
            returned: success
            type: str
            sample: www.sample.com
        content:
            description: The record content (details depend on record type).
            returned: success
            type: str
            sample: 192.0.2.91
        priority:
            description: Priority of the MX or SRV record.
            returned: success, if type is MX or SRV
            type: int
            sample: 10
        ttl:
            description: The time-to-live for the record.
            returned: success
            type: int
            sample: 3600
api_response:
    description: A dictionary containing the API response when an error occurrence.
    returned: failure
    type: str
'''

import traceback
from ansible.module_utils.basic import AnsibleModule, missing_required_lib

DOMROBOT_IMPORT_ERROR = None
try:
    import INWX.Domrobot
    from INWX.Domrobot import ApiClient, ApiType

    HAS_DOMROBOT_LIB = True
except ImportError:
    DOMROBOT_IMPORT_ERROR = traceback.format_exc()
    HAS_DOMROBOT_LIB = False


def convert_caa_record_to_type257(module):
    tag = module.params['tag']
    value = module.params['value']
    hex_length = len(tag) + len('"' + value + '"')

    flag = hex(int(module.params['flag']))[2:]
    if len(flag) == 1:
        flag = '0' + flag

    tag_length = hex(len(tag))[2:]
    if len(tag_length) == 1:
        tag_length = '0' + tag_length

    value = '\\# ' + str(hex_length) + ' ' + \
            flag + \
            tag_length + \
            tag.encode('ascii').hex() + value.encode('ascii').hex()
    return value


def build_record_afsdb(module):
    keys = ('service', 'value')
    return ' '.join(map(lambda key: str(module.params[key]), keys))


def build_record_caa(module):
    values = (module.params['flag'],
              module.params['tag'],
              '"' + module.params['value'] + '"')
    return ' '.join(map(str, values))


def build_record_naptr(module):
    values = (module.params['weight'],
              '"' + module.params['flag'] + '"',
              '"' + module.params['service'] + '"',
              module.params['regex'],
              module.params['substitution'])
    return ' '.join(map(str, values))


def build_record_srv(module):
    values = (module.params['weight'], module.params['port'], module.params['value'])
    return ' '.join(map(str, values))


def build_record_sshfp(module):
    keys = ('algorithm', 'hash_type', 'value')
    return ' '.join(map(lambda key: str(module.params[key]), keys))


def build_record_tlsa(module):
    keys = ('cert_usage', 'selector', 'hash_type', 'value')
    return ' '.join(map(lambda key: str(module.params[key]), keys))


def build_default_record(module):
    return module.params['value']


def build_record_content(module):
    switcher = {
        'A': build_default_record,
        'AAAA': build_default_record,
        'AFSDB': build_record_afsdb,
        'CAA': build_record_caa,
        'CNAME': build_default_record,
        'HINFO': build_default_record,
        'LOC': build_default_record,
        'MX': build_default_record,
        'NAPTR': build_record_naptr,
        'NS': build_default_record,
        'PTR': build_default_record,
        'RP': build_default_record,
        'SOA': build_default_record,
        'SRV': build_record_srv,
        'SSHFP': build_record_sshfp,
        'TLSA': build_record_tlsa,
        'TXT': build_default_record
    }

    return switcher.get(str(module.params['type']).upper())(module)


def get_record_fqdn(module):
    fqdn = ''
    if module.params['record'] and not module.params['record'].isspace() and module.params['record'] != '@':
        fqdn = module.params['record'] + '.'
    fqdn += module.params['domain']
    return fqdn


def check_present_state_required_arguments(module):
    required_params_for_type = {
        'A': ['value'],
        'AAAA': ['value'],
        'AFSDB': ['service', 'value'],
        'CAA': ['flag', 'tag', 'value'],
        'CNAME': ['value'],
        'HINFO': ['value'],
        'LOC': ['value'],
        'MX': ['priority', 'value'],
        'NAPTR': ['flag', 'service', 'regex', 'substitution'],
        'NS': ['value'],
        'PTR': ['value'],
        'RP': ['value'],
        'SOA': ['value'],
        'SRV': ['priority', 'port', 'value'],
        'SSHFP': ['algorithm', 'hash_type', 'value'],
        'TLSA': ['cert_usage', 'selector', 'hash_type', 'value'],
        'TXT': ['value']
    }

    unsatisfied_params = required_params_for_type[module.params['type']]

    for required_param in unsatisfied_params:
        if module.params.get(required_param, None) is not None:
            unsatisfied_params.remove(required_param)
        else:
            module.fail_json(msg='arguments missing for type ' + module.params['type']
                                 + ' record: ' + ' '.join(unsatisfied_params))
            return


def build_check_mode_record(module):
    return {
        'id': 0,
        'type': module.params['type'],
        'name': get_record_fqdn(module),
        'content': build_record_content(module),
        'priority': module.params['priority'],
        'ttl': module.params['ttl']
    }


def build_record_from_response(record_data):
    return {
        'id': record_data['id'],
        'type': record_data['type'],
        'name': record_data['name'],
        'content': record_data['content'],
        'priority': record_data['prio'],
        'ttl': record_data['ttl']
    }


def remove_dict_none_values(dictionary):
    filtered_dict = {}
    for key, value in dictionary.items():
        if value is not None:
            filtered_dict[key] = value
    return filtered_dict


def call_api_authenticated(module, method, params):
    client = ApiClient(api_type=ApiType.JSON_RPC, debug_mode=True)

    params['user'] = module.params['username']
    params['pass'] = module.params['password']

    params = remove_dict_none_values(params)
    return client.call_api(method, params)


def get_records(module):
    # hack for CAA search
    if module.params['type'] == 'CAA':
        content = convert_caa_record_to_type257(module)
    else:
        content = build_record_content(module)

    if module.params['type'] == 'SOA':
        result = call_api_authenticated(module, 'nameserver.info', {
            'domain': module.params['domain'],
            'type': module.params['type']
        })
    else:
        result = call_api_authenticated(module, 'nameserver.info', {
            'domain': module.params['domain'],
            'type': module.params['type'],
            'name': get_record_fqdn(module),
            'content': content
        })

    if result['code'] != 1000:
        module.fail_json(msg='API error.', result={'api_response': result})
        return None

    if result['resData'].get('record', None) is not None:
        # map all response records to internal record dicts
        records = list(map(build_record_from_response, result['resData']['record']))
        return records
    else:
        return None


def update_soa_record(module, record_id):
    result = call_api_authenticated(module, 'nameserver.updateRecord', {
        'id': record_id,
        'name': get_record_fqdn(module),
        'content': build_record_content(module),
        'ttl': module.params['ttl']
    })

    if result['code'] != 1000:
        module.fail_json(msg='API error.', result={'api_response': result})
        return None

    # fetch record again as the updated version should now be present
    return get_records(module)[0]


def update_record_ttl(module, record_id):
    result = call_api_authenticated(module, 'nameserver.updateRecord', {
        'id': record_id,
        'ttl': module.params['ttl']
    })

    if result['code'] != 1000:
        module.fail_json(msg='API error.', result={'api_response': result})

    # fetch record again as the updated version should now be present
    return get_records(module)[0]


def create_record(module):
    record_content = build_record_content(module)
    result = call_api_authenticated(module, 'nameserver.createRecord', {
        'domain': module.params['domain'],
        'type': module.params['type'],
        'content': record_content,
        'name': get_record_fqdn(module),
        'ttl': module.params['ttl'],
        'prio': module.params['priority']
    })

    if result['code'] != 1000:
        module.fail_json(msg='API error.', result={'api_response': result})
        return None

    # fetch record again as the updated version should now be present
    return get_records(module)[0]


def delete_record(module, record_id):
    call_api_authenticated(module, 'nameserver.deleteRecord', {'id': record_id})


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            algorithm=dict(type='int', required=False),
            flag=dict(type='str', required=False),
            tag=dict(type='str', required=False, choices=['issue', 'issuewild', 'iodef']),
            cert_usage=dict(type='int', required=False, choices=[0, 1, 2, 3]),
            domain=dict(type='str', required=True),
            hash_type=dict(type='int', required=False),
            regex=dict(type='str', required=False),
            password=dict(type='str', required=True, aliases=['pass'], no_log=True),
            priority=dict(type='int', required=False, default=1),
            port=dict(type='int', required=False),
            record=dict(type='str', required=False, default='', aliases=['name']),
            selector=dict(type='int', required=False, choices=[0, 1]),
            service=dict(type='str', required=False),
            state=dict(type='str', choices=['present', 'absent'], default='present'),
            substitution=dict(type='str', required=False),
            ttl=dict(type='int', required=False, default=86400),
            type=dict(type='str', required=True,
                      choices=['A', 'AAAA', 'AFSDB', 'CAA', 'CNAME', 'HINFO', 'LOC', 'MX',
                               'NAPTR', 'NS', 'PTR', 'RP', 'SOA', 'SRV', 'SSHFP', 'TLSA', 'TXT']),
            username=dict(type='str', required=True, aliases=['user']),
            value=dict(type='str', required=False, aliases=['content']),
            weight=dict(type='int', required=False, default=1),
        ),
        supports_check_mode=True,
        required_if=[
            ('state', 'absent', ['record']),
            ('state', 'present', ['record', 'type'])
        ]
    )

    if not HAS_DOMROBOT_LIB:
        module.fail_json(msg=missing_required_lib('inwx-domrobot'), exception=DOMROBOT_IMPORT_ERROR)

    found_records = get_records(module)

    if module.params['state'] == 'absent':
        if found_records:
            if module.params['type'] == 'SOA':
                module.fail_json(changed=False, msg="SOA record can only be updated.")
            else:
                # records exist, delete them if multiple match.
                if not module.check_mode:
                    for found_record in found_records:
                        delete_record(module, found_record['id'])
                module.exit_json(changed=True)
        else:
            # record doesn't exist, nothing to delete.
            module.exit_json(changed=False)
    elif module.params['state'] == 'present':
        check_present_state_required_arguments(module)
        if module.params['type'] == 'SOA':
            # can only be one
            soa_record = found_records[0]
            if soa_record['name'] == get_record_fqdn(module) \
                    and soa_record['content'] == build_record_content(module) \
                    and soa_record['ttl'] == module.params['ttl']:
                # record, content and ttl are equal, nothing changed.
                module.exit_json(changed=False, result={'record': soa_record})
            else:
                # record, content or ttl changed, update it.
                if module.check_mode:
                    updated_record = build_check_mode_record(module)
                else:
                    updated_record = update_soa_record(module, soa_record['id'])
                module.exit_json(changed=True, result={'record': updated_record})
        elif found_records:
            # should only contain one record
            found_record = found_records[0]
            if found_record['ttl'] != module.params['ttl']:
                # record exists but with another ttl. Update it.
                if module.check_mode:
                    updated_record = build_check_mode_record(module)
                else:
                    updated_record = update_record_ttl(module, found_record['id'])
                module.exit_json(changed=True, result={'record': updated_record})
            else:
                # identical record exists.
                module.exit_json(changed=False, result={'record': found_record})
        else:
            # record doesn't exist, create it.
            if module.check_mode:
                created_record = build_check_mode_record(module)
            else:
                created_record = create_record(module)
            module.exit_json(changed=True, result={'record': created_record})


def main():
    run_module()


if __name__ == '__main__':
    main()
