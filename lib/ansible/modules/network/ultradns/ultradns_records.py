#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Himanshu Pupneja <himanshu.pupneja@hotmail.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: ultradns_records
short_description: Manages record sets in ultradns
version_added: "2.10"
description:
  - Manages record sets in ultradns.
options:
  username:
    description:
      - Provide C(username) which will be required to authenticate with
        ultradns apis.
    type: str
    required: True
  password:
    description:
      - Provide C(username) which will be required to authenticate with
        ultradns apis.
    version_added: "2.10"
    type: str
    required: True
  use_http:
    description:
      - Whether you want to use C(http) or C(https)
    version_added: "2.10"
    type: str
    default: False
  domain:
    description:
      - Provide api domain of ultradns.
    type: str
    default: restapi.ultradns.com
    version_added: "2.10"
  zone_name:
    description:
      - Specifies the zone name where you want to add and delete record
        sets.
    type: str
    required: True
    version_added: "2.10"
  hostname:
    description:
      - The name of the host to be returned. The HostName is a C(FQDN). If
        FQDN is not provided then it will  append zone name with the host
        name.
    type: str
    required: True
    aliases: ['url']
    version_added: "2.10"
  ttl:
    description:
      - specifies expiration time(seconds) that is put on a DNS record.
    type: int
    default: 300
    version_added: "2.10"
  record_type:
    description:
        - The type of record set to create or delete.
    choices:
        - A
        - CNAME
    aliases: ['rtype']
    type: str
    version_added: "2.10"
    required: true
  points_to:
    description:
      - Specifies the address where dns should point.
    type: str
    required: True
    aliases: ['address']
    version_added: "2.10"
  state:
    description:
      - Specifies the current state of the record. C(present) creates
        the record or update records. C(absent) deletes the record.
    type: str
    choices:
      - present
      - absent
    default: present
    version_added: "2.10"
author:
  - Himanshu Pupneja (@Himanshu-pupneja)
'''

EXAMPLES = r'''
# Example to create A record
- name: create A record
  ultradns_records:
    username: admin
    password: secrets
    record_type: A
    zone_name: mytest-zone.com
    hostname: mytest
    ttl: 300
    points_to: 10.20.30.40
    state: present

# Example to Delete A record
- name: Delete A record
  ultradns_records:
    username: admin
    password: secrets
    record_type: A
    zone_name: mytest-zone.com
    hostname: mytest
    ttl: 300
    points_to: 10.20.30.40
    state: absent

# Example to update A record
- name: Update A record
  ultradns_records:
    username: admin
    password: secrets
    record_type: A
    zone_name: mytest-zone.com
    ttl: 500
    hostname: mytest
    points_to: 10.20.30.50
    state: present

# Example to create CNAME record
- name: create CNAME record
  ultradns_records:
    username: admin
    password: secrets
    record_type: CNAME
    zone_name: mytest-zone.com
    hostname: mytest
    ttl: 300
    points_to: myserver.domain.com
    state: present

# Example to Delete CNAME record
- name: Delete CNAME record
  ultradns_records:
    username: admin
    password: secrets
    record_type: CNAME
    zone_name: mytest-zone.com
    hostname: mytest
    ttl: 300
    points_to: myserver.domain.com
    state: absent

# Example to update CNAME record
- name: Update CNAME record
  ultradns_records:
    username: admin
    password: secrets
    record_type: CNAME
    zone_name: mytest-zone.com
    hostname: mytest
    ttl: 500
    points_to: myserver1.domain.com
    state: present
'''

RETURN = r'''
msg:
  description: return the message.
  type: str
  returned: always
'''

from ansible.module_utils.urls import urlparse
from ansible.module_utils.basic import AnsibleModule

try:
    import ultra_rest_client
    ULTRADNS_SDK = True
except ImportError:
    ULTRADNS_SDK = False


class Ultradns(object):
    """
    This is a class for performing operation on ultradns.
    Attributes:
        It uses attributes coming from ansible module class.
    """

    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.status = None
        self.username = self.params['username']
        self.password = self.params['password']
        self.domain = self.params['domain']
        self.use_http = self.params['use_http']
        self.zone_name = self.params['zone_name']
        self.record_type = self.params['record_type']
        self.hostname = self.params['hostname']
        self.ttl = self.params['ttl']
        self.points_to = self.params['points_to']
        self.ttl = self.params['ttl']
        self.state = self.params['state']
        self.api = ultra_rest_client

        if self.hostname.endswith(self.zone_name):
            pass
        else:
            self.hostname = "{0}.{1}".format(self.hostname, self.zone_name)

        # Fix hostname to remove http and https and just use the url
        if 'http' in self.hostname:
            self.hostname = urlparse(self.hostname).netloc

        if 'http' in self.points_to:
            self.points_to = urlparse(self.points_to).netloc

        # Result dict object to track status and outputs
        # Specific values are set for different function statuses
        # ( eg: login, cname record update etc.)
        self.result = dict(changed=False)

        # Login to dyn with credentials from the module
        self.client = self.connection()

    def connection(self):
        """ Connecting to ultradns api """
        try:
            client = self.api.RestApiClient(
                self.username, self.password, self.use_http == 'True', self.domain)
            return client
        except Exception as exc:
            message = "Connection error. {0}".format(exc)
            self.module.fail_json(msg=message)

    def check_zone_exist(self):
        """ Check if its a valid zone or not """
        result = self.client.get_zone_metadata(self.zone_name)
        if not isinstance(result, dict):
            message = result[0]["errorMessage"]
            self.module.fail_json(msg=message)

    def check_record_exist(self):
        """ Check if record already exist or not """
        result = self.client.get_rrsets_by_type(
            self.zone_name, self.record_type, {"owner": self.hostname})
        status = False
        record_data = {}
        if isinstance(result, dict):
            status = True
            record_data = result["rrSets"][0]
        else:
            if result[0]["errorMessage"] == "Data not found.":
                status = False
        return record_data, status

    def create_record(self):
        """ Create  a new record """
        result = self.client.create_rrset(
            self.zone_name, self.record_type, self.hostname, self.ttl, self.points_to)
        if isinstance(result, dict):
            if result["message"] == "Successful":
                self.result["changed"] = True
                self.result["msg"] = "Record created successfully"
        else:
            message = "Not able to create record. {0}".format(result)
            self.module.fail_json(msg=message)

    def update_record(self):
        """ Update the existing record """
        result = self.client.edit_rrset(
            self.zone_name, self.record_type, self.hostname, self.ttl, self.points_to)
        if isinstance(result, dict):
            if result["message"] == "Successful":
                self.result["changed"] = True
                self.result["msg"] = "Record updated successfully"
        else:
            message = "Not able to update record. {0}".format(result)
            self.module.fail_json(msg=message)

    def delete_record(self):
        """ Delete the record """
        result = self.client.delete_rrset(
            self.zone_name, self.record_type, self.hostname)
        if isinstance(result, dict):
            self.result["changed"] = True
            self.result["msg"] = "Record deleted successfully"
        else:
            message = "Not able to delete record. {0}".format(result)
            self.module.fail_json(msg=message)

    def main(self):
        """ create, update and delete records """
        self.result["msg"] = "Nothing is changed"

        version_details = self.client.version()
        if 'version' in version_details.keys():
            self.result["ud_version"] = version_details["version"]
        else:
            message = "ultradns version doesn't exist"
            self.module.fail_json(msg=message)

        account_details = self.client.get_account_details()

        account_names = []
        for account in account_details["accounts"]:
            account_names.append(account["accountName"])

        if account_names:
            self.result["ud_account_name"] = account_names
        else:
            message = "ultradns account name doesn't exist"
            self.module.fail_json(msg=message)

        self.check_zone_exist()

        record_data, self.status = self.check_record_exist()

        if self.status:
            # print("record exist")
            if self.state == "absent":
                # print("but state is absent")
                self.delete_record()
            else:
                address = "{0}.".format(self.points_to)
                existing_address = record_data["rdata"][0]
                if self.ttl == record_data["ttl"] and address == existing_address:
                    self.result["msg"] = "Record already exist"
                else:
                    self.update_record()
        else:
            # print("record doesn't exist")
            if self.state == "present":
                # print("but state is present")
                self.create_record()

        self.module.exit_json(**self.result)


def main():
    """ defining Ansible parameter and calling class Ultradns to do the job """
    module_args = dict(
        username=dict(required=True, type='str'),
        password=dict(required=True, no_log=True, type='str'),
        use_http=dict(default=False),
        domain=dict(default='restapi.ultradns.com'),
        zone_name=dict(required=True, type='str'),
        record_type=dict(
            required=True,
            type='str',
            aliases=['rtype'],
            choices=['CNAME', 'A']
        ),
        state=dict(choices=['present', 'absent'],
                   default='present', type='str'),
        hostname=dict(required=True, type='str', aliases=['url']),
        points_to=dict(required=True, aliases=['address']),
        ttl=dict(default='300', type='int'),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    try:
        if ULTRADNS_SDK == 'False':
            module.fail_json(msg="ultradns sdk is required for this module. Please install")
        Ultradns(module).main()
    except Exception as exc:
        message = "Something wrong happened. {0}".format(exc)
        module.fail_json(msg=message)


if __name__ == "__main__":
    main()
