#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: dnsmadeeasy
version_added: "1.3"
short_description: Interface with dnsmadeeasy.com (a DNS hosting service).
description:
   - >
     Manages DNS records via the v2 REST API of the DNS Made Easy service.  It handles records only; there is no manipulation of domains or
     monitor/account support yet. See: U(https://www.dnsmadeeasy.com/integration/restapi/)
options:
  account_key:
    description:
      - Account API Key.
    required: true

  account_secret:
    description:
      - Account Secret Key.
    required: true

  domain:
    description:
      - Domain to work with. Can be the domain name (e.g. "mydomain.com") or the numeric ID of the domain in DNS Made Easy (e.g. "839989") for faster
        resolution
    required: true

  record_name:
    description:
      - Record name to get/create/delete/update. If record_name is not specified; all records for the domain will be returned in "result" regardless
        of the state argument.

  record_type:
    description:
      - Record type.
    choices: [ 'A', 'AAAA', 'CNAME', 'ANAME', 'HTTPRED', 'MX', 'NS', 'PTR', 'SRV', 'TXT' ]

  record_value:
    description:
      - >
        Record value. HTTPRED: <redirection URL>, MX: <priority> <target name>, NS: <name server>, PTR: <target name>,
        SRV: <priority> <weight> <port> <target name>, TXT: <text value>"
      - >
        If record_value is not specified; no changes will be made and the record will be returned in 'result'
        (in other words, this module can be used to fetch a record's current id, type, and ttl)

  record_ttl:
    description:
      - record's "Time to live".  Number of seconds the record remains cached in DNS servers.
    default: 1800

  state:
    description:
      - whether the record should exist or not
    required: true
    choices: [ 'present', 'absent' ]

  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    type: bool
    default: 'yes'
    version_added: 1.5.1

  monitor:
    description:
      - If C(yes), add or change the monitor.  This is applicable only for A records.
    type: bool
    default: 'no'
    version_added: 2.4

  systemDescription:
    description:
      - Description used by the monitor.
    required: true
    default: ''
    version_added: 2.4

  maxEmails:
    description:
      - Number of emails sent to the contact list by the monitor.
    required: true
    default: 1
    version_added: 2.4

  protocol:
    description:
      - Protocol used by the monitor.
    required: true
    default: 'HTTP'
    choices: ['TCP', 'UDP', 'HTTP', 'DNS', 'SMTP', 'HTTPS']
    version_added: 2.4

  port:
    description:
      - Port used by the monitor.
    required: true
    default: 80
    version_added: 2.4

  sensitivity:
    description:
      - Number of checks the monitor performs before a failover occurs where Low = 8, Medium = 5,and High = 3.
    required: true
    default: 'Medium'
    choices: ['Low', 'Medium', 'High']
    version_added: 2.4

  contactList:
    description:
      - Name or id of the contact list that the monitor will notify.
      - The default C('') means the Account Owner.
    required: true
    default: ''
    version_added: 2.4

  httpFqdn:
    description:
      - The fully qualified domain name used by the monitor.
    version_added: 2.4

  httpFile:
    description:
      - The file at the Fqdn that the monitor queries for HTTP or HTTPS.
    version_added: 2.4

  httpQueryString:
    description:
      - The string in the httpFile that the monitor queries for HTTP or HTTPS.
    version_added: 2.4

  failover:
    description:
      - If C(yes), add or change the failover.  This is applicable only for A records.
    type: bool
    default: 'no'
    version_added: 2.4

  autoFailover:
    description:
      - If true, fallback to the primary IP address is manual after a failover.
      - If false, fallback to the primary IP address is automatic after a failover.
    type: bool
    default: 'no'
    version_added: 2.4

  ip1:
    description:
      - Primary IP address for the failover.
      - Required if adding or changing the monitor or failover.
    version_added: 2.4

  ip2:
    description:
      - Secondary IP address for the failover.
      - Required if adding or changing the failover.
    version_added: 2.4

  ip3:
    description:
      - Tertiary IP address for the failover.
    version_added: 2.4

  ip4:
    description:
      - Quaternary IP address for the failover.
    version_added: 2.4

  ip5:
    description:
      - Quinary IP address for the failover.
    version_added: 2.4

notes:
  - The DNS Made Easy service requires that machines interacting with the API have the proper time and timezone set. Be sure you are within a few
    seconds of actual time by using NTP.
  - This module returns record(s) and monitor(s) in the "result" element when 'state' is set to 'present'.
    These values can be be registered and used in your playbooks.
  - Only A records can have a monitor or failover.
  - To add failover, the 'failover', 'autoFailover', 'port', 'protocol', 'ip1', and 'ip2' options are required.
  - To add monitor, the 'monitor', 'port', 'protocol', 'maxEmails', 'systemDescription', and 'ip1' options are required.
  - The monitor and the failover will share 'port', 'protocol', and 'ip1' options.

requirements: [ hashlib, hmac ]
author: "Brice Burgess (@briceburg)"
'''

EXAMPLES = '''
# fetch my.com domain records
- dnsmadeeasy:
    account_key: key
    account_secret: secret
    domain: my.com
    state: present
  register: response

# create / ensure the presence of a record
- dnsmadeeasy:
    account_key: key
    account_secret: secret
    domain: my.com
    state: present
    record_name: test
    record_type: A
    record_value: 127.0.0.1

# update the previously created record
- dnsmadeeasy:
    account_key: key
    account_secret: secret
    domain: my.com
    state: present
    record_name: test
    record_value: 192.0.2.23

# fetch a specific record
- dnsmadeeasy:
    account_key: key
    account_secret: secret
    domain: my.com
    state: present
    record_name: test
  register: response

# delete a record / ensure it is absent
- dnsmadeeasy:
    account_key: key
    account_secret: secret
    domain: my.com
    record_type: A
    state: absent
    record_name: test

# Add a failover
- dnsmadeeasy:
    account_key: key
    account_secret: secret
    domain: my.com
    state: present
    record_name: test
    record_type: A
    record_value: 127.0.0.1
    failover: True
    ip1: 127.0.0.2
    ip2: 127.0.0.3

- dnsmadeeasy:
    account_key: key
    account_secret: secret
    domain: my.com
    state: present
    record_name: test
    record_type: A
    record_value: 127.0.0.1
    failover: True
    ip1: 127.0.0.2
    ip2: 127.0.0.3
    ip3: 127.0.0.4
    ip4: 127.0.0.5
    ip5: 127.0.0.6

# Add a monitor
- dnsmadeeasy:
    account_key: key
    account_secret: secret
    domain: my.com
    state: present
    record_name: test
    record_type: A
    record_value: 127.0.0.1
    monitor: yes
    ip1: 127.0.0.2
    protocol: HTTP  # default
    port: 80  # default
    maxEmails: 1
    systemDescription: Monitor Test A record
    contactList: my contact list

# Add a monitor with http options
- dnsmadeeasy:
    account_key: key
    account_secret: secret
    domain: my.com
    state: present
    record_name: test
    record_type: A
    record_value: 127.0.0.1
    monitor: yes
    ip1: 127.0.0.2
    protocol: HTTP  # default
    port: 80  # default
    maxEmails: 1
    systemDescription: Monitor Test A record
    contactList: 1174  # contact list id
    httpFqdn: http://my.com
    httpFile: example
    httpQueryString: some string

# Add a monitor and a failover
- dnsmadeeasy:
    account_key: key
    account_secret: secret
    domain: my.com
    state: present
    record_name: test
    record_type: A
    record_value: 127.0.0.1
    failover: True
    ip1: 127.0.0.2
    ip2: 127.0.0.3
    monitor: yes
    protocol: HTTPS
    port: 443
    maxEmails: 1
    systemDescription: monitoring my.com status
    contactList: emergencycontacts

# Remove a failover
- dnsmadeeasy:
    account_key: key
    account_secret: secret
    domain: my.com
    state: present
    record_name: test
    record_type: A
    record_value: 127.0.0.1
    failover: no

# Remove a monitor
- dnsmadeeasy:
    account_key: key
    account_secret: secret
    domain: my.com
    state: present
    record_name: test
    record_type: A
    record_value: 127.0.0.1
    monitor: no
'''

# ============================================
# DNSMadeEasy module specific support methods.
#

import json
import hashlib
import hmac
from time import strftime, gmtime

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.six import string_types


class DME2(object):

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
        self.contactList_map = None  # ["contactList_name"] => ID

        # Lookup the domain ID if passed as a domain name vs. ID
        if not self.domain.isdigit():
            self.domain = self.getDomainByName(self.domain)['id']

        self.record_url = 'dns/managed/' + str(self.domain) + '/records'
        self.monitor_url = 'monitor'
        self.contactList_url = 'contactList'

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
        if data and not isinstance(data, string_types):
            data = urlencode(data)

        response, info = fetch_url(self.module, url, data=data, method=method, headers=self._headers())
        if info['status'] not in (200, 201, 204):
            self.module.fail_json(msg="%s returned %s, with body: %s" % (url, info['status'], info['msg']))

        try:
            return json.load(response)
        except Exception:
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

        if record_type in ["CNAME", "ANAME", "HTTPRED", "PTR"]:
            for result in self.all_records:
                if result['name'] == record_name and result['type'] == record_type:
                    return result
            return False
        elif record_type in ["A", "AAAA", "MX", "NS", "TXT", "SRV"]:
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
        # @TODO cache this call so it's executed only once per ansible execution
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
        # @TODO update the cache w/ resultant record + id when impleneted
        return self.query(self.record_url, 'POST', data)

    def updateRecord(self, record_id, data):
        # @TODO update the cache w/ resultant record + id when impleneted
        return self.query(self.record_url + '/' + str(record_id), 'PUT', data)

    def deleteRecord(self, record_id):
        # @TODO remove record from the cache when impleneted
        return self.query(self.record_url + '/' + str(record_id), 'DELETE')

    def getMonitor(self, record_id):
        return self.query(self.monitor_url + '/' + str(record_id), 'GET')

    def updateMonitor(self, record_id, data):
        return self.query(self.monitor_url + '/' + str(record_id), 'PUT', data)

    def prepareMonitor(self, data):
        return json.dumps(data, separators=(',', ':'))

    def getContactList(self, contact_list_id):
        if not self.contactList_map:
            self._instMap('contactList')

        return self.contactLists.get(contact_list_id, False)

    def getContactlists(self):
        return self.query(self.contactList_url, 'GET')['data']

    def getContactListByName(self, name):
        if not self.contactList_map:
            self._instMap('contactList')

        return self.getContactList(self.contactList_map.get(name, 0))

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
                             'A', 'AAAA', 'CNAME', 'ANAME', 'HTTPRED', 'MX', 'NS', 'PTR', 'SRV', 'TXT']),
            record_value=dict(required=False),
            record_ttl=dict(required=False, default=1800, type='int'),
            monitor=dict(default='no', type='bool'),
            systemDescription=dict(default=''),
            maxEmails=dict(default=1, type='int'),
            protocol=dict(default='HTTP', choices=['TCP', 'UDP', 'HTTP', 'DNS', 'SMTP', 'HTTPS']),
            port=dict(default=80, type='int'),
            sensitivity=dict(default='Medium', choices=['Low', 'Medium', 'High']),
            contactList=dict(default=None),
            httpFqdn=dict(required=False),
            httpFile=dict(required=False),
            httpQueryString=dict(required=False),
            failover=dict(default='no', type='bool'),
            autoFailover=dict(default='no', type='bool'),
            ip1=dict(required=False),
            ip2=dict(required=False),
            ip3=dict(required=False),
            ip4=dict(required=False),
            ip5=dict(required=False),
            validate_certs=dict(default='yes', type='bool'),
        ),
        required_together=(
            ['record_value', 'record_ttl', 'record_type']
        ),
        required_if=[
            ['failover', True, ['autoFailover', 'port', 'protocol', 'ip1', 'ip2']],
            ['monitor', True, ['port', 'protocol', 'maxEmails', 'systemDescription', 'ip1']]
        ]
    )

    protocols = dict(TCP=1, UDP=2, HTTP=3, DNS=4, SMTP=5, HTTPS=6)
    sensitivities = dict(Low=8, Medium=5, High=3)

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

    # Fetch existing monitor if the A record indicates it should exist and build the new monitor
    current_monitor = dict()
    new_monitor = dict()
    if current_record and current_record['type'] == 'A':
        current_monitor = DME.getMonitor(current_record['id'])

    # Build the new monitor
    for i in ['monitor', 'systemDescription', 'protocol', 'port', 'sensitivity', 'maxEmails',
              'contactList', 'httpFqdn', 'httpFile', 'httpQueryString',
              'failover', 'autoFailover', 'ip1', 'ip2', 'ip3', 'ip4', 'ip5']:
        if module.params[i] is not None:
            if i == 'protocol':
                # The API requires protocol to be a numeric in the range 1-6
                new_monitor['protocolId'] = protocols[module.params[i]]
            elif i == 'sensitivity':
                # The API requires sensitivity to be a numeric of 8, 5, or 3
                new_monitor[i] = sensitivities[module.params[i]]
            elif i == 'contactList':
                # The module accepts either the name or the id of the contact list
                contact_list_id = module.params[i]
                if not contact_list_id.isdigit() and contact_list_id != '':
                    contact_list = DME.getContactListByName(contact_list_id)
                    if not contact_list:
                        module.fail_json(msg="Contact list {} does not exist".format(contact_list_id))
                    contact_list_id = contact_list.get('id', '')
                new_monitor['contactListId'] = contact_list_id
            else:
                # The module option names match the API field names
                new_monitor[i] = module.params[i]

    # Compare new record against existing one
    record_changed = False
    if current_record:
        for i in new_record:
            if str(current_record[i]) != str(new_record[i]):
                record_changed = True
        new_record['id'] = str(current_record['id'])

    monitor_changed = False
    if current_monitor:
        for i in new_monitor:
            if str(current_monitor.get(i)) != str(new_monitor[i]):
                monitor_changed = True

    # Follow Keyword Controlled Behavior
    if state == 'present':
        # return the record if no value is specified
        if "value" not in new_record:
            if not current_record:
                module.fail_json(
                    msg="A record with name '%s' does not exist for domain '%s.'" % (record_name, module.params['domain']))
            module.exit_json(changed=False, result=dict(record=current_record, monitor=current_monitor))

        # create record and monitor as the record does not exist
        if not current_record:
            record = DME.createRecord(DME.prepareRecord(new_record))
            monitor = DME.updateMonitor(record['id'], DME.prepareMonitor(new_monitor))
            module.exit_json(changed=True, result=dict(record=record, monitor=monitor))

        # update the record
        updated = False
        if record_changed:
            DME.updateRecord(current_record['id'], DME.prepareRecord(new_record))
            updated = True
        if monitor_changed:
            DME.updateMonitor(current_monitor['recordId'], DME.prepareMonitor(new_monitor))
            updated = True
        if updated:
            module.exit_json(changed=True, result=dict(record=new_record, monitor=new_monitor))

        # return the record (no changes)
        module.exit_json(changed=False, result=dict(record=current_record, monitor=current_monitor))

    elif state == 'absent':
        changed = False
        # delete the record (and the monitor/failover) if it exists
        if current_record:
            DME.deleteRecord(current_record['id'])
            module.exit_json(changed=True)

        # record does not exist, return w/o change.
        module.exit_json(changed=changed)

    else:
        module.fail_json(
            msg="'%s' is an unknown value for the state argument" % state)


if __name__ == '__main__':
    main()
