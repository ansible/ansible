#!/usr/bin/env python


'''
Dynamic inventory script that prints inventory based on the '/inventory/devices' api call
to Arista Cloud Vision Portal. This script requires cvprac "pip install cvprac".

You can run the following:

cvp_inventory.py --list
cvp_inventory.py -- host <hostname>

examples:

cvp_inventory.py --list 

{  
   "cvp":[  
      "sw1",
      "sw2"
   ],
   "_meta":{  
      "hostvars":{  
         "sw1":{  
            "hostname":"sw1",
            "ansible_host":"192.0.2.1",
            "serialnumber":"123456789",
            "modelname":"DCS-7020TR-48",
            "softwareversion":"4.20.8M"
         },
         "sw2":{  
            "hostname":"sw2",
            "ansible_host":"192.0.2.2",
            "serialnumber":"987654321",
            "modelname":"DCS-7020TR-48",
            "softwareversion":"4.20.8M"
         }
      }
   }
}

cvp_inventory.py --host sw1

{  
   "hostname":"sw1",
   "ipAddress":"192.0.2.1",
   "serialNumber":"123456789",
   "modelName":"DCS-7020TR-48",
   "version":"4.20.8M"
}

'''

import json
from cvprac.cvp_client import CvpClient
import sys
import urllib3
import argparse

urllib3.disable_warnings()

CVP_SERVER = '192.0.2.254'
CVP_USER = 'username'
CVP_PASS = 'password'

_key = 'cvp'

_cvp_to_ansible = [('hostname', 'hostname'),
                    ('ipAddress', 'ansible_host'),
                    ('serialNumber', 'serialnumber'),
                    ("modelName", 'modelname'),
                    ("version", 'softwareversion')]

def get_cvpinventory():
    """Pulls inventory from CVP"""
    client = CvpClient()
    client.connect([CVP_SERVER], CVP_USER, CVP_PASS)
    result = client.get('/inventory/devices')
    host_dict = {}
    for host in result:
        host_dict[host['hostname']] = {
            'hostname': host['hostname'],
            'ipAddress': host['ipAddress'],
            'serialNumber': host['serialNumber'],
            'modelName': host['modelName'],
            'version': host['version']
        }
    return(host_dict)


def print_inventory():
    """Prints out json formated inventory"""
    inventory = get_cvpinventory()
    meta = {'hostvars': {}}
    for key, value in inventory.items():
        tmp_dict = {}
        for cvp_opt, ans_opt in _cvp_to_ansible:
            val = value[cvp_opt]
            tmp_dict[ans_opt] = val
        if tmp_dict:
            meta['hostvars'][key] = tmp_dict
    print(json.dumps({_key: list(set(meta['hostvars'].keys())), '_meta': meta}))


def print_host(host):
    inv = get_cvpinventory()
    print(json.dumps(inv[host]))


def get_args(args_list):
    parser = argparse.ArgumentParser(
        description='ansible inventory script parsing CVP API')
    mutex_group = parser.add_mutually_exclusive_group(required=True)
    help_list = 'list all hosts from CVP inventory'
    mutex_group.add_argument('--list', action='store_true', help=help_list)
    help_host = 'display variables for a host'
    mutex_group.add_argument('--host', help=help_host)
    return parser.parse_args(args_list)


def main(args_list):

    args = get_args(args_list)
    if args.list:
        print_inventory()
    if args.host:
        print_host(args.host)


if __name__ == '__main__':
    main(sys.argv[1:])
