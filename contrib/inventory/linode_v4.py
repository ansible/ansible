#!/usr/bin/env python3

# (c) 2017, Will Weber
#
# This file is part of Ansible,
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

'''
Linode external inventory script for the v4 api
===============================================

Generates inventory that Ansible can understand by making API requests to
Linode using the v4 linode api. Also exposes compatibility with the legacy api.

Executes quickly by leveraging two API calls for legacy and one call for the
v4 api.

In order to interact with either api, you must export LINODE_API_KEY with your
personal access token.

In order to generate a key for the legacy api, you must do so on the old
manager; https://manager.linode.com. Likewise goes for the v4 api, you must go
here: https://cloud.linode.com.

By default, will only show running instances. You can export LINODE_ALL to 
target all linodes associated with your account.

By default, will use the v4 API. You can export LINODE_LEGACY to use the legacy
API.

Output currently looks like this for the v4 api:
{
  "_meta": {
    "hostvars": {
      "test": {
        "public_ip": "172.100.1.1",
        "ansible_host": "172.104.1.1",
        "ansible_ssh_host": "172.104.1.1",
        "linode_id": 383000,
        "status": "running",
        "distro": "linode/debian9",
        "group": "some_group",
        "ipv6": "2600:3903::fffc:ffff:ff25:ef9d/64",
        "region": "us-east-1a"
      }
    }
  },
  "": [
    "test"
  ]
}

Legacy output:
{
  "_meta": {
    "hostvars": {
      "test": {
        "public_ip": "172.100.1.1",
        "ansible_host": "172.100.1.1",
        "ansible_ssh_host": "172.101.1.1",
        "linode_id": 383000,
        "status": "Running",
        "distro": "Debian",
        "datacenter": "newark"
      }
    }
  },
  "": [
    "test"
  ]
}

It can be used like so with a playbook:

ansible-playbook -i contrib/inventory/linode_v4.py test.yml -K
'''

import argparse
import os
import http.client
import json
import sys

def _empty_inventory():
    return {"_meta": {"hostvars": {}}}

def linode_status(status_id):
    enum = {
            -1: "Being Created",
             0: "Brand New",
             1: "Running",
             2: "Powered Off",
           }
    return enum[status_id]

def datacenter_lookup(dc_id):
    enum = {
      	    2: "dallas",
            3: "fremont",
      	    4: "atlanta",
            6: "newark",
            7: "london",
	    8: "tokyo",
	    9: "singapore",
   	   10: "frankfurt",
           11: "shinagawa1",
           }
    return enum[dc_id]

def call(legacy, all_linodes, token):
    '''
    Communicate to the Linode API.
    Supports the ability to communicate to the current and legacy api's.
    '''
    ansible_vars_dict = {"_meta": {"hostvars": {}}}
    conn = http.client.HTTPSConnection("api.linode.com")
    if legacy:
        conn.request("GET", "/?api_key={}&api_action=linode.ip.list".format(
            token))
        response = conn.getresponse()
        
        # check if status code not OK, though it seems to always return 200s...
        if response.status != 200:
            conn.close()
            ansible_vars_dict['_meta']['error'] = {
                "status_code": response.status,
                "reason": response.reason,
            }
            return ansible_vars_dict

        ip_dict = json.loads(response.read())

        # check if error returned from linode api
        if len(ip_dict["ERRORARRAY"]) != 0:
            conn.close()
            ansible_vars_dict['_meta']['error'] = {
                "reason": ip_dict["ERRORARRAY"],
            }
            return ansible_vars_dict

        else:
            conn.request("GET", "/?api_key={}&api_action=linode.list".format(
                token))
            response = conn.getresponse()
            lin_dict = json.loads(response.read())
            ansible_vars_dict['_meta']['hostvars'] = {
                elem['LABEL']: {
                    "public_ip": ipitem['IPADDRESS'],
                    "ansible_host": ipitem['IPADDRESS'],
                    "ansible_ssh_host": ipitem['IPADDRESS'],
                    "linode_id": ipitem["LINODEID"],
                    "status": linode_status(elem["STATUS"]),
                    "distro": elem["DISTRIBUTIONVENDOR"],
                    "datacenter": datacenter_lookup(elem["DATACENTERID"]),
                }
                # 2 dimensional iteration to gather as many facts as possible
                # about the linodes listed on the account.
                for elem in lin_dict["DATA"] for ipitem in ip_dict["DATA"]
                # filter linodes by those running or when all_linodes is true
                # return only unique ones.
                if ipitem["LINODEID"] == elem["LINODEID"] and 
                (linode_status(elem["STATUS"]) == "Running") or
                ipitem["LINODEID"] == elem["LINODEID"] and all_linodes
            }
        ansible_vars_dict[""] = list(
                ansible_vars_dict['_meta']['hostvars'].keys())
        return ansible_vars_dict

    else:
        conn.request("GET", "/v4/linode/instances",
                headers={"Authorization": "Bearer {}".format(token)})
        response = conn.getresponse()
        if response.status != 200:
            conn.close()
            ansible_vars_dict['_meta']['error'] = {
                "status_code": response.status,
                "reason": response.reason,
            }
            return ansible_vars_dict
        resp_json = json.loads(response.read())
        ansible_vars_dict['_meta']['hostvars'] = {
                datum['label']: {
                    "public_ip": datum['ipv4'][0],
                    "ansible_host": datum['ipv4'][0],
                    "ansible_ssh_host": datum['ipv4'][0],
                    "linode_id": datum['id'],
                    "status": datum['status'],
                    "distro": datum['distribution'],
                    "group": datum['group'],
                    "ipv6": datum['ipv6'],
                    "region": datum['region'],
                }
            for datum in resp_json['data']
            if datum['status'] == 'running' or all_linodes
        }
        ansible_vars_dict[""] = list(
                ansible_vars_dict['_meta']['hostvars'].keys())
        return ansible_vars_dict

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description='dynamic inventory based on Linode APIs')
    parser.add_argument('--list', action='store_true', default=True,
                        help='Show instances')
    p = parser.parse_args()

    try:
        legacy = os.environ['LINODE_LEGACY']
    except KeyError as e:
        legacy = False

    try:
        all_linodes = os.environ['LINODE_ALL']
    except KeyError as e:
        all_linodes = False

    try:
        token = os.environ['LINODE_API_KEY']
    except KeyError as e:
        print('Please export LINODE_API_KEY')
        sys.exit(1)
    print(json.dumps(call(legacy, all_linodes, token)))
