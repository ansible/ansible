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
---
module: dnsimple
version_added: "1.6"
short_description: Interface with dnsimple.com (a DNS hosting service).
description:
   - "Manages domains and records via the DNSimple API, see the docs: U(http://developer.dnsimple.com/)"
options:
  account_email:
    description:
      - "Account email. If omitted, the env variables DNSIMPLE_EMAIL and DNSIMPLE_API_TOKEN will be looked for. If those aren't found, a C(.dnsimple) file will be looked for, see: U(https://github.com/mikemaccana/dnsimple-python#getting-started)"
    required: false
    default: null

  account_api_token:
    description:
      - Account API token. See I(account_email) for info.
    required: false
    default: null      

  domain:
    description:
      - Domain to work with. Can be the domain name (e.g. "mydomain.com") or the numeric ID of the domain in DNSimple. If omitted, a list of domains will be returned.
      - If domain is present but the domain doesn't exist, it will be created.
    required: false
    default: null

  record:
    description:
      - Record to add, if blank a record for the domain will be created, supports the wildcard (*)
    required: false
    default: null

  record_ids:
    description:
      - List of records to ensure they either exist or don't exist
    required: false
    default: null

  type:
    description:
      - The type of DNS record to create
    required: false
    choices: [ 'A', 'ALIAS', 'CNAME', 'MX', 'SPF', 'URL', 'TXT', 'NS', 'SRV', 'NAPTR', 'PTR', 'AAAA', 'SSHFP', 'HINFO', 'POOL' ]
    default: null

  ttl:
    description:
      - The TTL to give the new record
    required: false
    default: 3600 (one hour)

  value:
    description: 
      - Record value
      - "Must be specified when trying to ensure a record exists"
    required: false
    default: null

  priority:
    description:
      - Record priority
    required: false
    default: null

  state:
    description:
      - whether the record should exist or not
    required: false
    choices: [ 'present', 'absent' ]
    default: null

  solo:
    description:
      - Whether the record should be the only one for that record type and record name. Only use with state=present on a record
    required: false
    default: null

requirements: [ dnsimple ]
author: Alex Coomans
'''

EXAMPLES = '''
# authenticate using email and API token
- local_action: dnsimple account_email=test@example.com account_api_token=dummyapitoken

# fetch all domains
- local_action dnsimple
  register: domains

# fetch my.com domain records
- local_action: dnsimple domain=my.com state=present
  register: records

# delete a domain
- local_action: dnsimple domain=my.com state=absent

# create a test.my.com A record to point to 127.0.0.01
- local_action: dnsimple domain=my.com record=test type=A value=127.0.0.1
  register: record

# and then delete it
- local_action: dnsimple domain=my.com record_ids={{ record['id'] }}

# create a my.com CNAME record to example.com
- local_action: dnsimple domain=my.com record= type=CNAME value=example.com state=present

# change it's ttl
- local_action: dnsimple domain=my.com record= type=CNAME value=example.com ttl=600 state=present

# and delete the record
- local_action: dnsimpledomain=my.com record= type=CNAME value=example.com state=absent

'''

import os
try:
    from dnsimple import DNSimple
    from dnsimple.dnsimple import DNSimpleException
except ImportError:
    print "failed=True msg='dnsimple required for this module'"
    sys.exit(1)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            account_email     = dict(required=False),
            account_api_token = dict(required=False, no_log=True),
            domain            = dict(required=False),
            record            = dict(required=False),
            record_ids        = dict(required=False, type='list'),
            type              = dict(required=False, choices=['A', 'ALIAS', 'CNAME', 'MX', 'SPF', 'URL', 'TXT', 'NS', 'SRV', 'NAPTR', 'PTR', 'AAAA', 'SSHFP', 'HINFO', 'POOL']),
            ttl               = dict(required=False, default=3600, type='int'),
            value             = dict(required=False),
            priority          = dict(required=False, type='int'), 
            state             = dict(required=False, choices=['present', 'absent']),
            solo              = dict(required=False, type='bool'),
        ),
        required_together = (
            ['record', 'value']
        ),
        supports_check_mode = True,
    )

    account_email     = module.params.get('account_email')
    account_api_token = module.params.get('account_api_token')
    domain            = module.params.get('domain')
    record            = module.params.get('record')
    record_ids        = module.params.get('record_ids')
    record_type       = module.params.get('type')
    ttl               = module.params.get('ttl')
    value             = module.params.get('value')
    priority          = module.params.get('priority')
    state             = module.params.get('state')
    is_solo           = module.params.get('solo')

    if account_email and account_api_token:
        client = DNSimple(email=account_email, api_token=account_api_token)
    elif os.environ.get('DNSIMPLE_EMAIL') and os.environ.get('DNSIMPLE_API_TOKEN'):
        client = DNSimple(email=os.environ.get('DNSIMPLE_EMAIL'), api_token=os.environ.get('DNSIMPLE_API_TOKEN'))
    else:
        client = DNSimple()

    try:
        # Let's figure out what operation we want to do

        # No domain, return a list
        if not domain:
            domains = client.domains()
            module.exit_json(changed=False, result=[d['domain'] for d in domains])

        # Domain & No record
        if domain and record is None and not record_ids:
            domains = [d['domain'] for d in client.domains()]
            if domain.isdigit():
                dr = next((d for d in domains if d['id'] == int(domain)), None)
            else:
                dr = next((d for d in domains if d['name'] == domain), None)
            if state == 'present':
                if dr:
                    module.exit_json(changed=False, result=dr)
                else:
                    if module.check_mode:
                        module.exit_json(changed=True)
                    else:
                        module.exit_json(changed=True, result=client.add_domain(domain)['domain'])
            elif state == 'absent':
                if dr:
                    if not module.check_mode:
                        client.delete(domain)
                    module.exit_json(changed=True)
                else:
                    module.exit_json(changed=False)
            else:
                module.fail_json(msg="'%s' is an unknown value for the state argument" % state)

        # need the not none check since record could be an empty string
        if domain and record is not None:
            records = [r['record'] for r in client.records(str(domain))]

            if not record_type:
                module.fail_json(msg="Missing the record type")

            if not value:
                module.fail_json(msg="Missing the record value")

            rr = next((r for r in records if r['name'] == record and r['record_type'] == record_type and r['content'] == value), None)

            if state == 'present':
                changed = False
                if is_solo:
                    # delete any records that have the same name and record type
                    same_type = [r['id'] for r in records if r['name'] == record and r['record_type'] == record_type]
                    if rr:
                        same_type = [rid for rid in same_type if rid != rr['id']]
                    if same_type:
                        if not module.check_mode:
                            for rid in same_type:
                                client.delete_record(str(domain), rid)
                        changed = True
                if rr:
                    # check if we need to update
                    if rr['ttl'] != ttl or rr['prio'] != priority:
                        data = {}
                        if ttl:      data['ttl']  = ttl
                        if priority: data['prio'] = priority
                        if module.check_mode:
                            module.exit_json(changed=True)
                        else:
                            module.exit_json(changed=True, result=client.update_record(str(domain), str(rr['id']), data)['record'])
                    else:
                        module.exit_json(changed=changed, result=rr)
                else:
                    # create it
                    data = {
                        'name':        record,
                        'record_type': record_type,
                        'content':     value,
                    }
                    if ttl:      data['ttl']  = ttl
                    if priority: data['prio'] = priority
                    if module.check_mode:
                        module.exit_json(changed=True)
                    else:
                        module.exit_json(changed=True, result=client.add_record(str(domain), data)['record'])
            elif state == 'absent':
                if rr:
                    if not module.check_mode:
                        client.delete_record(str(domain), rr['id'])
                    module.exit_json(changed=True)
                else:
                    module.exit_json(changed=False)
            else:
                module.fail_json(msg="'%s' is an unknown value for the state argument" % state)

        # Make sure these record_ids either all exist or none
        if domain and record_ids:
            current_records = [str(r['record']['id']) for r in client.records(str(domain))]
            wanted_records  = [str(r) for r in record_ids]
            if state == 'present':
                difference = list(set(wanted_records) - set(current_records))
                if difference:
                    module.fail_json(msg="Missing the following records: %s" % difference)
                else:
                    module.exit_json(changed=False)
            elif state == 'absent':
                difference = list(set(wanted_records) & set(current_records))
                if difference:
                    if not module.check_mode:
                        for rid in difference:
                            client.delete_record(str(domain), rid)
                    module.exit_json(changed=True)
                else:
                    module.exit_json(changed=False)
            else:
                module.fail_json(msg="'%s' is an unknown value for the state argument" % state)

    except DNSimpleException, e:
        module.fail_json(msg="Unable to contact DNSimple: %s" % e.message)

    module.fail_json(msg="Unknown what you wanted me to do")

# import module snippets
from ansible.module_utils.basic import *

main()
