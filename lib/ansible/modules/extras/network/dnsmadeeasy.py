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
module: dnsmadeeasy
version_added: "1.3"
short_description: Interface with dnsmadeeasy.com (a DNS hosting service).
description:
   - "Manages DNS records via the v2 REST API of the DNS Made Easy service.  It handles records only; there is no manipulation of domains or monitor/account support yet. See: U(http://www.dnsmadeeasy.com/services/rest-api/)"
options:
  account_key:
    description:
      - Accout API Key.
    required: true
    default: null
    
  account_secret:
    description:
      - Accout Secret Key.
    required: true
    default: null
    
  domain:
    description:
      - Domain to work with. Can be the domain name (e.g. "mydomain.com") or the numeric ID of the domain in DNS Made Easy (e.g. "839989") for faster resolution.
    required: true
    default: null
    
  record_name:
    description:
      - Record name to get/create/delete/update. If record_name is not specified; all records for the domain will be returned in "result" regardless of the state argument.
    required: false
    default: null
    
  record_type:
    description:
      - Record type.
    required: false
    choices: [ 'A', 'AAAA', 'CNAME', 'HTTPRED', 'MX', 'NS', 'PTR', 'SRV', 'TXT' ]
    default: null

  record_value:
    description: 
      - "Record value. HTTPRED: <redirection URL>, MX: <priority> <target name>, NS: <name server>, PTR: <target name>, SRV: <priority> <weight> <port> <target name>, TXT: <text value>"
      - "If record_value is not specified; no changes will be made and the record will be returned in 'result' (in other words, this module can be used to fetch a record's current id, type, and ttl)"
    required: false
    default: null
    
  record_ttl:
    description:
      - record's "Time to live".  Number of seconds the record remains cached in DNS servers.
    required: false
    default: 1800
    
  state:
    description:
      - whether the record should exist or not
    required: true
    choices: [ 'present', 'absent' ]
    default: null
    
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    required: false
    default: 'yes'
    choices: ['yes', 'no']
    version_added: 1.5.1

notes:
  - The DNS Made Easy service requires that machines interacting with the API have the proper time and timezone set. Be sure you are within a few seconds of actual time by using NTP. 
  - This module returns record(s) in the "result" element when 'state' is set to 'present'. This value can be be registered and used in your playbooks.
  
requirements: [ hashlib, hmac ]
author: "Brice Burgess (@briceburg)"
'''

EXAMPLES = '''
# fetch my.com domain records
- dnsmadeeasy: account_key=key account_secret=secret domain=my.com state=present
  register: response
  
# create / ensure the presence of a record
- dnsmadeeasy: account_key=key account_secret=secret domain=my.com state=present record_name="test" record_type="A" record_value="127.0.0.1"

# update the previously created record
- dnsmadeeasy: account_key=key account_secret=secret domain=my.com state=present record_name="test" record_value="192.168.0.1"

# fetch a specific record
- dnsmadeeasy: account_key=key account_secret=secret domain=my.com state=present record_name="test"
  register: response
  
# delete a record / ensure it is absent
- dnsmadeeasy: account_key=key account_secret=secret domain=my.com state=absent record_name="test"
'''

# ============================================
# DNSMadeEasy module specific support methods.
#

import urllib

IMPORT_ERROR = None
try:
    import json
    from time import strftime, gmtime
    import hashlib
    import hmac
except ImportError, e:
    IMPORT_ERROR = str(e)

class DME2:

    def __init__(self, apikey, secret, domain, module):
        self.module = module

        self.api = apikey
        self.secret = secret
        self.baseurl = 'https://api.dnsmadeeasy.com/V2.0/'
        self.domain = str(domain)
        self.domain_map = None      # ["domain_name"] => ID
        self.record_map = None      # ["record_name"] => ID
        self.records = None         # ["record_ID"] => <record>
        self.all_records = None

        # Lookup the domain ID if passed as a domain name vs. ID
        if not self.domain.isdigit():
            self.domain = self.getDomainByName(self.domain)['id']

        self.record_url = 'dns/managed/' + str(self.domain) + '/records'

    def _headers(self):
        currTime = self._get_date()
        hashstring = self._create_hash(currTime)
        headers = {'x-dnsme-apiKey': self.api,
                   'x-dnsme-hmac': hashstring,
                   'x-dnsme-requestDate': currTime,
                   'content-type': 'application/json'}
        return headers

    def _get_date(self):
        return strftime("%a, %d %b %Y %H:%M:%S GMT", gmtime())

    def _create_hash(self, rightnow):
        return hmac.new(self.secret.encode(), rightnow.encode(), hashlib.sha1).hexdigest()

    def query(self, resource, method, data=None):
        url = self.baseurl + resource
        if data and not isinstance(data, basestring):
            data = urllib.urlencode(data)

        response, info = fetch_url(self.module, url, data=data, method=method, headers=self._headers())
        if info['status'] not in (200, 201, 204):
            self.module.fail_json(msg="%s returned %s, with body: %s" % (url, info['status'], info['msg']))

        try:
            return json.load(response)
        except Exception, e:
            return {}

    def getDomain(self, domain_id):
        if not self.domain_map:
            self._instMap('domain')

        return self.domains.get(domain_id, False)

    def getDomainByName(self, domain_name):
        if not self.domain_map:
            self._instMap('domain')

        return self.getDomain(self.domain_map.get(domain_name, 0))

    def getDomains(self):
        return self.query('dns/managed', 'GET')['data']

    def getRecord(self, record_id):
        if not self.record_map:
            self._instMap('record')

        return self.records.get(record_id, False)

    # Try to find a single record matching this one.
    # How we do this depends on the type of record. For instance, there
    # can be several MX records for a single record_name while there can
    # only be a single CNAME for a particular record_name. Note also that
    # there can be several records with different types for a single name.
    def getMatchingRecord(self, record_name, record_type, record_value):
        # Get all the records if not already cached
        if not self.all_records:
            self.all_records = self.getRecords()

        if record_type in ["A", "AAAA", "CNAME", "HTTPRED", "PTR"]:
            for result in self.all_records:
                if result['name'] == record_name and result['type'] == record_type:
                    return result
            return False
        elif record_type in ["MX", "NS", "TXT", "SRV"]:
            for result in self.all_records:
                if record_type == "MX":
                    value = record_value.split(" ")[1]
                elif record_type == "SRV":
                    value = record_value.split(" ")[3]
                else:
                    value = record_value
                if result['name'] == record_name and result['type'] == record_type and result['value'] == value:
                    return result
            return False
        else:
            raise Exception('record_type not yet supported')

    def getRecords(self):
        return self.query(self.record_url, 'GET')['data']

    def _instMap(self, type):
        #@TODO cache this call so it's executed only once per ansible execution
        map = {}
        results = {}

        # iterate over e.g. self.getDomains() || self.getRecords()
        for result in getattr(self, 'get' + type.title() + 's')():

            map[result['name']] = result['id']
            results[result['id']] = result

        # e.g. self.domain_map || self.record_map
        setattr(self, type + '_map', map)
        setattr(self, type + 's', results)  # e.g. self.domains || self.records

    def prepareRecord(self, data):
        return json.dumps(data, separators=(',', ':'))

    def createRecord(self, data):
        #@TODO update the cache w/ resultant record + id when impleneted
        return self.query(self.record_url, 'POST', data)

    def updateRecord(self, record_id, data):
        #@TODO update the cache w/ resultant record + id when impleneted
        return self.query(self.record_url + '/' + str(record_id), 'PUT', data)

    def deleteRecord(self, record_id):
        #@TODO remove record from the cache when impleneted
        return self.query(self.record_url + '/' + str(record_id), 'DELETE')


# ===========================================
# Module execution.
#

def main():

    module = AnsibleModule(
        argument_spec=dict(
            account_key=dict(required=True),
            account_secret=dict(required=True, no_log=True),
            domain=dict(required=True),
            state=dict(required=True, choices=['present', 'absent']),
            record_name=dict(required=False),
            record_type=dict(required=False, choices=[
                             'A', 'AAAA', 'CNAME', 'HTTPRED', 'MX', 'NS', 'PTR', 'SRV', 'TXT']),
            record_value=dict(required=False),
            record_ttl=dict(required=False, default=1800, type='int'),
            validate_certs = dict(default='yes', type='bool'),
        ),
        required_together=(
            ['record_value', 'record_ttl', 'record_type']
        )
    )

    if IMPORT_ERROR:
        module.fail_json(msg="Import Error: " + IMPORT_ERROR)

    DME = DME2(module.params["account_key"], module.params[
               "account_secret"], module.params["domain"], module)
    state = module.params["state"]
    record_name = module.params["record_name"]
    record_type = module.params["record_type"]
    record_value = module.params["record_value"]

    # Follow Keyword Controlled Behavior
    if record_name is None:
        domain_records = DME.getRecords()
        if not domain_records:
            module.fail_json(
                msg="The requested domain name is not accessible with this api_key; try using its ID if known.")
        module.exit_json(changed=False, result=domain_records)

    # Fetch existing record + Build new one
    current_record = DME.getMatchingRecord(record_name, record_type, record_value)
    new_record = {'name': record_name}
    for i in ["record_value", "record_type", "record_ttl"]:
        if not module.params[i] is None:
            new_record[i[len("record_"):]] = module.params[i]
    # Special handling for mx record
    if new_record["type"] == "MX":
        new_record["mxLevel"] = new_record["value"].split(" ")[0]
        new_record["value"] = new_record["value"].split(" ")[1]

    # Special handling for SRV records
    if new_record["type"] == "SRV":
        new_record["priority"] = new_record["value"].split(" ")[0]
        new_record["weight"] = new_record["value"].split(" ")[1]
        new_record["port"] = new_record["value"].split(" ")[2]
        new_record["value"] = new_record["value"].split(" ")[3]

    # Compare new record against existing one
    changed = False
    if current_record:
        for i in new_record:
            if str(current_record[i]) != str(new_record[i]):
                changed = True
        new_record['id'] = str(current_record['id'])

    # Follow Keyword Controlled Behavior
    if state == 'present':
        # return the record if no value is specified
        if not "value" in new_record:
            if not current_record:
                module.fail_json(
                    msg="A record with name '%s' does not exist for domain '%s.'" % (record_name, module.params['domain']))
            module.exit_json(changed=False, result=current_record)

        # create record as it does not exist
        if not current_record:
            record = DME.createRecord(DME.prepareRecord(new_record))
            module.exit_json(changed=True, result=record)

        # update the record
        if changed:
            DME.updateRecord(
                current_record['id'], DME.prepareRecord(new_record))
            module.exit_json(changed=True, result=new_record)

        # return the record (no changes)
        module.exit_json(changed=False, result=current_record)

    elif state == 'absent':
        # delete the record if it exists
        if current_record:
            DME.deleteRecord(current_record['id'])
            module.exit_json(changed=True)

        # record does not exist, return w/o change.
        module.exit_json(changed=False)

    else:
        module.fail_json(
            msg="'%s' is an unknown value for the state argument" % state)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

main()
