#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016 Michael Gruener <michael.gruener@chaosmoon.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cloudflare_dns
author: "Michael Gruener (@mgruener)"
requirements:
   - "python >= 2.6"
version_added: "2.1"
short_description: manage Cloudflare DNS records
description:
   - "Manages dns records via the Cloudflare API, see the docs: U(https://api.cloudflare.com/)"
options:
  account_api_token:
    description:
      - >
        Account API token. You can obtain your API key from the bottom of the Cloudflare 'My Account' page, found here: U(https://www.cloudflare.com/a/account)
    required: true
  account_email:
    description:
      - "Account email."
    required: true
  port:
    description: Service port. Required for C(type=SRV)
    required: false
    default: null
  priority:
    description: Record priority. Required for C(type=MX) and C(type=SRV)
    required: false
    default: "1"
  proto:
    description: Service protocol. Required for C(type=SRV)
    required: false
    choices: [ 'tcp', 'udp' ]
    default: null
  proxied:
    description: Proxy through cloudflare network or just use DNS
    required: false
    default: no
    version_added: "2.3"
  record:
    description:
      - Record to add. Required if C(state=present). Default is C(@) (e.g. the zone name)
    required: false
    default: "@"
    aliases: [ "name" ]
  service:
    description: Record service. Required for C(type=SRV)
    required: false
    default: null
  solo:
    description:
      - Whether the record should be the only one for that record type and record name. Only use with C(state=present)
      - This will delete all other records with the same record name and type.
    required: false
    default: null
  state:
    description:
      - Whether the record(s) should exist or not
    required: false
    choices: [ 'present', 'absent' ]
    default: present
  timeout:
    description:
      - Timeout for Cloudflare API calls
    required: false
    default: 30
  ttl:
    description:
      - The TTL to give the new record. Must be between 120 and 2,147,483,647 seconds, or 1 for automatic.
    required: false
    default: 1 (automatic)
  type:
    description:
      - The type of DNS record to create. Required if C(state=present)
    required: false
    choices: [ 'A', 'AAAA', 'CNAME', 'TXT', 'SRV', 'MX', 'NS', 'SPF' ]
    default: null
  value:
    description:
      - The record value. Required for C(state=present)
    required: false
    default: null
    aliases: [ "content" ]
  weight:
    description: Service weight. Required for C(type=SRV)
    required: false
    default: "1"
  zone:
    description:
      - The name of the Zone to work with (e.g. "example.com"). The Zone must already exist.
    required: true
    aliases: ["domain"]
'''

EXAMPLES = '''
# create a test.my.com A record to point to 127.0.0.1
- cloudflare_dns:
    zone: my.com
    record: test
    type: A
    value: 127.0.0.1
    account_email: test@example.com
    account_api_token: dummyapitoken
  register: record

# create a my.com CNAME record to example.com
- cloudflare_dns:
    zone: my.com
    type: CNAME
    value: example.com
    state: present
    account_email: test@example.com
    account_api_token: dummyapitoken

# change it's ttl
- cloudflare_dns:
    zone: my.com
    type: CNAME
    value: example.com
    ttl: 600
    state: present
    account_email: test@example.com
    account_api_token: dummyapitoken

# and delete the record
- cloudflare_dns:
    zone: my.com
    type: CNAME
    value: example.com
    state: absent
    account_email: test@example.com
    account_api_token: dummyapitoken

# create a my.com CNAME record to example.com and proxy through cloudflare's network
- cloudflare_dns:
    zone: my.com
    type: CNAME
    value: example.com
    state: present
    proxied: yes
    account_email: test@example.com
    account_api_token: dummyapitoken

# create TXT record "test.my.com" with value "unique value"
# delete all other TXT records named "test.my.com"
- cloudflare_dns:
    domain: my.com
    record: test
    type: TXT
    value: unique value
    state: present
    solo: true
    account_email: test@example.com
    account_api_token: dummyapitoken

# create a SRV record _foo._tcp.my.com
- cloudflare_dns:
    domain: my.com
    service: foo
    proto: tcp
    port: 3500
    priority: 10
    weight: 20
    type: SRV
    value: fooserver.my.com
'''

RETURN = '''
record:
    description: dictionary containing the record data
    returned: success, except on record deletion
    type: complex
    contains:
        content:
            description: the record content (details depend on record type)
            returned: success
            type: string
            sample: 192.0.2.91
        created_on:
            description: the record creation date
            returned: success
            type: string
            sample: 2016-03-25T19:09:42.516553Z
        data:
            description: additional record data
            returned: success, if type is SRV
            type: dictionary
            sample: {
                name: "jabber",
                port: 8080,
                priority: 10,
                proto: "_tcp",
                service: "_xmpp",
                target: "jabberhost.sample.com",
                weight: 5,
            }
        id:
            description: the record id
            returned: success
            type: string
            sample: f9efb0549e96abcb750de63b38c9576e
        locked:
            description: No documentation available
            returned: success
            type: boolean
            sample: False
        meta:
            description: No documentation available
            returned: success
            type: dictionary
            sample: { auto_added: false }
        modified_on:
            description: record modification date
            returned: success
            type: string
            sample: 2016-03-25T19:09:42.516553Z
        name:
            description: the record name as FQDN (including _service and _proto for SRV)
            returned: success
            type: string
            sample: www.sample.com
        priority:
            description: priority of the MX record
            returned: success, if type is MX
            type: int
            sample: 10
        proxiable:
            description: whether this record can be proxied through cloudflare
            returned: success
            type: boolean
            sample: False
        proxied:
            description: whether the record is proxied through cloudflare
            returned: success
            type: boolean
            sample: False
        ttl:
            description: the time-to-live for the record
            returned: success
            type: int
            sample: 300
        type:
            description: the record type
            returned: success
            type: string
            sample: A
        zone_id:
            description: the id of the zone containing the record
            returned: success
            type: string
            sample: abcede0bf9f0066f94029d2e6b73856a
        zone_name:
            description: the name of the zone containing the record
            returned: success
            type: string
            sample: sample.com
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url


class CloudflareAPI(object):

    cf_api_endpoint = 'https://api.cloudflare.com/client/v4'
    changed = False

    def __init__(self, module):
        self.module            = module
        self.account_api_token = module.params['account_api_token']
        self.account_email     = module.params['account_email']
        self.port              = module.params['port']
        self.priority          = module.params['priority']
        self.proto             = module.params['proto']
        self.proxied           = module.params['proxied']
        self.record            = module.params['record']
        self.service           = module.params['service']
        self.is_solo           = module.params['solo']
        self.state             = module.params['state']
        self.timeout           = module.params['timeout']
        self.ttl               = module.params['ttl']
        self.type              = module.params['type']
        self.value             = module.params['value']
        self.weight            = module.params['weight']
        self.zone              = module.params['zone']

        if self.record == '@':
            self.record = self.zone

        if (self.type in ['CNAME','NS','MX','SRV']) and (self.value is not None):
            self.value = self.value.rstrip('.')

        if (self.type == 'SRV'):
            if (self.proto is not None) and (not self.proto.startswith('_')):
                self.proto = '_' + self.proto
            if (self.service is not None) and (not self.service.startswith('_')):
                self.service = '_' + self.service

        if not self.record.endswith(self.zone):
            self.record = self.record + '.' + self.zone

    def _cf_simple_api_call(self,api_call,method='GET',payload=None):
        headers = { 'X-Auth-Email': self.account_email,
                    'X-Auth-Key': self.account_api_token,
                    'Content-Type': 'application/json' }
        data = None
        if payload:
            try:
                data = json.dumps(payload)
            except Exception as e:
                self.module.fail_json(msg="Failed to encode payload as JSON: %s " % to_native(e))

        resp, info = fetch_url(self.module,
                               self.cf_api_endpoint + api_call,
                               headers=headers,
                               data=data,
                               method=method,
                               timeout=self.timeout)

        if info['status'] not in [200,304,400,401,403,429,405,415]:
            self.module.fail_json(msg="Failed API call {0}; got unexpected HTTP code {1}".format(api_call,info['status']))

        error_msg = ''
        if info['status'] == 401:
            # Unauthorized
            error_msg = "API user does not have permission; Status: {0}; Method: {1}: Call: {2}".format(info['status'],method,api_call)
        elif info['status'] == 403:
            # Forbidden
            error_msg = "API request not authenticated; Status: {0}; Method: {1}: Call: {2}".format(info['status'],method,api_call)
        elif info['status'] == 429:
            # Too many requests
            error_msg = "API client is rate limited; Status: {0}; Method: {1}: Call: {2}".format(info['status'],method,api_call)
        elif info['status'] == 405:
            # Method not allowed
            error_msg = "API incorrect HTTP method provided; Status: {0}; Method: {1}: Call: {2}".format(info['status'],method,api_call)
        elif info['status'] == 415:
            # Unsupported Media Type
            error_msg = "API request is not valid JSON; Status: {0}; Method: {1}: Call: {2}".format(info['status'],method,api_call)
        elif info ['status'] == 400:
            # Bad Request
            error_msg = "API bad request; Status: {0}; Method: {1}: Call: {2}".format(info['status'],method,api_call)

        result = None
        try:
            content = resp.read()
        except AttributeError:
            if info['body']:
                content = info['body']
            else:
                error_msg += "; The API response was empty"

        if content:
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                error_msg += "; Failed to parse API response: {0}".format(content)

        # received an error status but no data with details on what failed
        if (info['status'] not in [200,304]) and (result is None):
            self.module.fail_json(msg=error_msg)

        if not result['success']:
            error_msg += "; Error details: "
            for error in result['errors']:
                error_msg += "code: {0}, error: {1}; ".format(error['code'],error['message'])
                if 'error_chain' in error:
                    for chain_error in error['error_chain']:
                        error_msg += "code: {0}, error: {1}; ".format(chain_error['code'],chain_error['message'])
            self.module.fail_json(msg=error_msg)

        return result, info['status']

    def _cf_api_call(self,api_call,method='GET',payload=None):
        result, status = self._cf_simple_api_call(api_call,method,payload)

        data = result['result']

        if 'result_info' in result:
            pagination = result['result_info']
            if pagination['total_pages'] > 1:
                next_page = int(pagination['page']) + 1
                parameters = ['page={0}'.format(next_page)]
                # strip "page" parameter from call parameters (if there are any)
                if '?' in api_call:
                    raw_api_call,query = api_call.split('?',1)
                    parameters += [param for param in query.split('&') if not param.startswith('page')]
                else:
                    raw_api_call = api_call
                while next_page <= pagination['total_pages']:
                    raw_api_call += '?' + '&'.join(parameters)
                    result, status = self._cf_simple_api_call(raw_api_call,method,payload)
                    data += result['result']
                    next_page += 1

        return data, status

    def _get_zone_id(self,zone=None):
        if not zone:
            zone = self.zone

        zones = self.get_zones(zone)
        if len(zones) > 1:
            self.module.fail_json(msg="More than one zone matches {0}".format(zone))

        if len(zones) < 1:
            self.module.fail_json(msg="No zone found with name {0}".format(zone))

        return zones[0]['id']

    def get_zones(self,name=None):
        if not name:
            name = self.zone
        param = ''
        if name:
            param = '?' + urlencode({'name' : name})
        zones,status = self._cf_api_call('/zones' + param)
        return zones

    def get_dns_records(self,zone_name=None,type=None,record=None,value=''):
        if not zone_name:
            zone_name = self.zone
        if not type:
            type = self.type
        if not record:
            record = self.record
        # necessary because None as value means to override user
        # set module value
        if (not value) and (value is not None):
            value = self.value

        zone_id = self._get_zone_id()
        api_call = '/zones/{0}/dns_records'.format(zone_id)
        query = {}
        if type:
            query['type'] = type
        if record:
            query['name'] = record
        if value:
            query['content'] = value
        if query:
            api_call += '?' + urlencode(query)

        records,status = self._cf_api_call(api_call)
        return records

    def delete_dns_records(self,**kwargs):
        params = {}
        for param in ['port','proto','service','solo','type','record','value','weight','zone']:
            if param in kwargs:
                params[param] = kwargs[param]
            else:
                params[param] = getattr(self,param)

        records = []
        content = params['value']
        search_record = params['record']
        if params['type'] == 'SRV':
            content = str(params['weight']) + '\t' + str(params['port']) + '\t' + params['value']
            search_record = params['service'] + '.' + params['proto'] + '.' + params['record']
        if params['solo']:
            search_value = None
        else:
            search_value = content

        records = self.get_dns_records(params['zone'],params['type'],search_record,search_value)

        for rr in records:
            if params['solo']:
                if not ((rr['type'] == params['type']) and (rr['name'] == search_record) and (rr['content'] == content)):
                    self.changed = True
                    if not self.module.check_mode:
                        result, info = self._cf_api_call('/zones/{0}/dns_records/{1}'.format(rr['zone_id'],rr['id']),'DELETE')
            else:
                self.changed = True
                if not self.module.check_mode:
                    result, info = self._cf_api_call('/zones/{0}/dns_records/{1}'.format(rr['zone_id'],rr['id']),'DELETE')
        return self.changed

    def ensure_dns_record(self,**kwargs):
        params = {}
        for param in ['port','priority','proto','proxied','service','ttl','type','record','value','weight','zone']:
            if param in kwargs:
                params[param] = kwargs[param]
            else:
                params[param] = getattr(self,param)

        search_value = params['value']
        search_record = params['record']
        new_record = None
        if (params['type'] is None) or (params['record'] is None):
            self.module.fail_json(msg="You must provide a type and a record to create a new record")

        if (params['type'] in [ 'A','AAAA','CNAME','TXT','MX','NS','SPF']):
            if not params['value']:
                self.module.fail_json(msg="You must provide a non-empty value to create this record type")

            # there can only be one CNAME per record
            # ignoring the value when searching for existing
            # CNAME records allows us to update the value if it
            # changes
            if params['type'] == 'CNAME':
                search_value = None

            new_record = {
                "type": params['type'],
                "name": params['record'],
                "content": params['value'],
                "ttl": params['ttl']
            }

        if (params['type'] in [ 'A', 'AAAA', 'CNAME' ]):
            new_record["proxied"] = params["proxied"]

        if params['type'] == 'MX':
            for attr in [params['priority'],params['value']]:
                if (attr is None) or (attr == ''):
                    self.module.fail_json(msg="You must provide priority and a value to create this record type")
            new_record = {
                "type": params['type'],
                "name": params['record'],
                "content": params['value'],
                "priority": params['priority'],
                "ttl": params['ttl']
            }

        if params['type'] == 'SRV':
            for attr in [params['port'],params['priority'],params['proto'],params['service'],params['weight'],params['value']]:
                if (attr is None) or (attr == ''):
                    self.module.fail_json(msg="You must provide port, priority, proto, service, weight and a value to create this record type")
            srv_data = {
                "target": params['value'],
                "port": params['port'],
                "weight": params['weight'],
                "priority": params['priority'],
                "name": params['record'][:-len('.' + params['zone'])],
                "proto": params['proto'],
                "service": params['service']
            }
            new_record = { "type": params['type'], "ttl": params['ttl'], 'data': srv_data }
            search_value = str(params['weight']) + '\t' + str(params['port']) + '\t' + params['value']
            search_record = params['service'] + '.' + params['proto'] + '.' + params['record']

        zone_id = self._get_zone_id(params['zone'])
        records = self.get_dns_records(params['zone'],params['type'],search_record,search_value)
        # in theory this should be impossible as cloudflare does not allow
        # the creation of duplicate records but lets cover it anyways
        if len(records) > 1:
            self.module.fail_json(msg="More than one record already exists for the given attributes. That should be impossible, please open an issue!")
        # record already exists, check if it must be updated
        if len(records) == 1:
            cur_record = records[0]
            do_update = False
            if (params['ttl'] is not None) and (cur_record['ttl'] != params['ttl'] ):
                do_update = True
            if (params['priority'] is not None) and ('priority' in cur_record) and (cur_record['priority'] != params['priority']):
                do_update = True
            if ('data' in new_record) and ('data' in cur_record):
                if (cur_record['data'] > new_record['data']) - (cur_record['data'] < new_record['data']):
                    do_update = True
            if (type == 'CNAME') and (cur_record['content'] != new_record['content']):
                do_update = True
            if do_update:
                if self.module.check_mode:
                    result = new_record
                else:
                    result, info = self._cf_api_call('/zones/{0}/dns_records/{1}'.format(zone_id,records[0]['id']),'PUT',new_record)
                self.changed = True
                return result,self.changed
            else:
                return records,self.changed
        if self.module.check_mode:
            result = new_record
        else:
            result, info = self._cf_api_call('/zones/{0}/dns_records'.format(zone_id),'POST',new_record)
        self.changed = True
        return result,self.changed

def main():
    module = AnsibleModule(
        argument_spec = dict(
            account_api_token = dict(required=True, no_log=True, type='str'),
            account_email     = dict(required=True, type='str'),
            port              = dict(required=False, default=None, type='int'),
            priority          = dict(required=False, default=1, type='int'),
            proto             = dict(required=False, default=None, choices=[ 'tcp', 'udp' ], type='str'),
            proxied           = dict(required=False, default=False, type='bool'),
            record            = dict(required=False, default='@', aliases=['name'], type='str'),
            service           = dict(required=False, default=None, type='str'),
            solo              = dict(required=False, default=None, type='bool'),
            state             = dict(required=False, default='present', choices=['present', 'absent'], type='str'),
            timeout           = dict(required=False, default=30, type='int'),
            ttl               = dict(required=False, default=1, type='int'),
            type              = dict(required=False, default=None, choices=[ 'A', 'AAAA', 'CNAME', 'TXT', 'SRV', 'MX', 'NS', 'SPF' ], type='str'),
            value             = dict(required=False, default=None, aliases=['content'], type='str'),
            weight            = dict(required=False, default=1, type='int'),
            zone              = dict(required=True, default=None, aliases=['domain'], type='str'),
        ),
        supports_check_mode = True,
        required_if = ([
            ('state','present',['record','type']),
            ('type','MX',['priority','value']),
            ('type','SRV',['port','priority','proto','service','value','weight']),
            ('type','A',['value']),
            ('type','AAAA',['value']),
            ('type','CNAME',['value']),
            ('type','TXT',['value']),
            ('type','NS',['value']),
            ('type','SPF',['value'])
        ]
        ),
        required_one_of = (
            [['record','value','type']]
        )
    )

    changed = False
    cf_api = CloudflareAPI(module)

    # sanity checks
    if cf_api.is_solo and cf_api.state == 'absent':
        module.fail_json(msg="solo=true can only be used with state=present")

    # perform add, delete or update (only the TTL can be updated) of one or
    # more records
    if cf_api.state == 'present':
        # delete all records matching record name + type
        if cf_api.is_solo:
            changed = cf_api.delete_dns_records(solo=cf_api.is_solo)
        result,changed = cf_api.ensure_dns_record()
        if isinstance(result,list):
            module.exit_json(changed=changed,result={'record': result[0]})
        else:
            module.exit_json(changed=changed,result={'record': result})
    else:
        # force solo to False, just to be sure
        changed = cf_api.delete_dns_records(solo=False)
        module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
