#!/usr/bin/env python
'''
Ansible Inventory Script

Makes some API calls to api.vult.com/v1 to get information about servers and dumps them as json
eg. ./vultr --host server.example.com

{
    "server.example.com: {
        "hosts": [
            "X.X.X.X"
        ]
    }
}

'''
from __future__ import print_function
import argparse
import os
import json
import sys
import requests
VULTR_API_URL = "https://api.vultr.com/v1/server/list"

class VultrInventory(object):
    def __init__(self):
        self.inventory = {}
        self.key = ""
        self.check_key_exist()
        self.parse_args()

        if self.args.host:
            self.get_server_info()
        if self.args.list:
            self.get_all()

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on Vultr')
        parser.add_argument('--list', action='store_true', help='List nodes')
        parser.add_argument('--host', action='store', help='Get all the variables about a specific node')
        self.args = parser.parse_args()

    def get_all(self):
        req = requests.get(VULTR_API_URL, headers={"API-Key" : self.key})

        if req.status_code == 403: #IP not allowed to access API
            print("Please make sure you current IP is whitelisted here https://my.vultr.com/settings/#settingsapi", file=sys.stderr)
            sys.exit(-1)
        elif req.status_code == 200:
            hostvars = {"hostvars" : {}}
            self.inventory = {"_meta": hostvars}
            servers = req.json()
            for x in servers:
                location = servers[x]["location"].lower().replace(" ", "_")
                if location not in self.inventory:
                    self.inventory[location] = {"hosts" : [servers[x]["label"]]}
                else:
                    self.inventory[location]["hosts"].append(servers[x]["label"])
                hostvars["hostvars"][servers[x]["label"]] = {
                    "ansible_ssh_host" : servers[x]["main_ip"],
                    "vultr_os": servers[x]["os"],
                    "vultr_tag": servers[x]["tag"],
                    "vultr_cost_per_month": servers[x]["cost_per_month"],
                    "vultr_server_state": servers[x]["server_state"],
                    "vultr_internal_ip": servers[x]["internal_ip"],
                    "vultr_disk": servers[x]["disk"],
                    "vultr_v6_main_ip": servers[x]["v6_main_ip"],
                    "vultr_power_status": servers[x]["power_status"],
                    "vultr_ram": servers[x]["ram"],
                    "vultr_allowed_bandwidth_gb": servers[x]["allowed_bandwidth_gb"],
                    "vultr_auto_backups": servers[x]["auto_backups"],
                    "vultr_status": servers[x]["status"],
                    "vultr_date_created": servers[x]["date_created"],
                    "vultr_netmask_v4": servers[x]["netmask_v4"],
                    "vultr_kvm_url": servers[x]["kvm_url"],
                    "vultr_vcpu_count": servers[x]["vcpu_count"],
                    "vultr_APPID": servers[x]["APPID"],
                    "vultr_DCID": servers[x]["DCID"],
                    "vultr_OSID": servers[x]["OSID"],
                    "vultr_SUBID": servers[x]["SUBID"],
                    "vultr_VPSPLANID": servers[x]["VPSPLANID"],
                    "vultr_current_bandwidth_gb": servers[x]["current_bandwidth_gb"],
                    "vultr_gateway_v4": servers[x]["gateway_v4"],
                    "vultr_default_password": servers[x]["default_password"],
                    "vultr_pending_charges": servers[x]["pending_charges"],
                    "vultr_v6_network": servers[x]["v6_network"],
                    "vultr_v6_network_size": servers[x]["v6_network_size"],
                    "vultr_v6_networks": servers[x]["v6_networks"]

                }
            json.dump(self.inventory, sys.stdout)

    def get_server_info(self):
        req = requests.get(VULTR_API_URL, headers={"API-Key" : self.key})

        if req.status_code == 403: #IP not allowed to access API
            print("Please make sure you current IP is whitelisted here https://my.vultr.com/settings/#settingsapi",
                  file=sys.stderr)
            sys.exit(-1)
        elif req.status_code == 200:
            servers = req.json()
            x = [x for x in servers if servers[x]["label"] == self.args.host]

            if len(x) > 0:
                json.dump(servers[x[0]], sys.stdout)
            else:
                json.dump({}, sys.stdout)
    def check_key_exist(self):
        if os.environ.get("VULTR_API_KEY"):
            self.key = os.environ.get("VULTR_API_KEY")
        else:
            print("Couldn't find VULTR_API_KEY environment variable, Please export your key eg. export VULTR_API_KEY=<Your API KEY>", file=sys.stderr)
            sys.exit(os.EX_CONFIG)

VultrInventory()
