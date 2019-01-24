#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2018, Yanis Guenane <yanis+ansible@guenane.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: vultr_server_facts
short_description: Gather facts about the Vultr servers available.
description:
  - Gather facts about servers available.
version_added: "2.7"
author: "Yanis Guenane (@Spredzy)"
extends_documentation_fragment: vultr
'''

EXAMPLES = r'''
- name: Gather Vultr servers facts
  local_action:
    module: vultr_server_facts

- name: Print the gathered facts
  debug:
    var: ansible_facts.vultr_server_facts
'''

RETURN = r'''
---
vultr_api:
  description: Response from Vultr API with a few additions/modification
  returned: success
  type: complex
  contains:
    api_account:
      description: Account used in the ini file to select the key
      returned: success
      type: str
      sample: default
    api_timeout:
      description: Timeout used for the API requests
      returned: success
      type: int
      sample: 60
    api_retries:
      description: Amount of max retries for the API requests
      returned: success
      type: int
      sample: 5
    api_endpoint:
      description: Endpoint used for the API requests
      returned: success
      type: str
      sample: "https://api.vultr.com"
vultr_server_facts:
  description: Response from Vultr API
  returned: success
  type: complex
  contains:
    "vultr_server_facts": [
      {
        "allowed_bandwidth_gb": 1000,
        "auto_backup_enabled": false,
        "application": null,
        "cost_per_month": 5.00,
        "current_bandwidth_gb": 0,
        "date_created": "2018-07-19 08:23:03",
        "default_password": "p4ssw0rd!",
        "disk": "Virtual 25 GB",
        "firewallgroup": null,
        "id": 17241096,
        "internal_ip": "",
        "kvm_url": "https://my.vultr.com/subs/vps/novnc/api.php?data=OFB...",
        "name": "ansibletest",
        "os": "CentOS 7 x64",
        "pending_charges": 0.01,
        "plan": "1024 MB RAM,25 GB SSD,1.00 TB BW",
        "power_status": "running",
        "ram": "1024 MB",
        "region": "Amsterdam",
        "server_state": "ok",
        "status": "active",
        "tag": "",
        "v4_gateway": "105.178.158.1",
        "v4_main_ip": "105.178.158.181",
        "v4_netmask": "255.255.254.0",
        "v6_main_ip": "",
        "v6_network": "",
        "v6_network_size": "",
        "v6_networks": [],
        "vcpu_count": 1
      }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vultr import (
    Vultr,
    vultr_argument_spec,
)


class AnsibleVultrServerFacts(Vultr):

    def __init__(self, module):
        super(AnsibleVultrServerFacts, self).__init__(module, "vultr_server_facts")

        self.returns = {
            "APPID": dict(key='application', convert_to='int', transform=self._get_application_name),
            "FIREWALLGROUPID": dict(key='firewallgroup', transform=self._get_firewallgroup_name),
            "SUBID": dict(key='id', convert_to='int'),
            "VPSPLANID": dict(key='plan', convert_to='int', transform=self._get_plan_name),
            "allowed_bandwidth_gb": dict(convert_to='int'),
            'auto_backups': dict(key='auto_backup_enabled', convert_to='bool'),
            "cost_per_month": dict(convert_to='float'),
            "current_bandwidth_gb": dict(convert_to='float'),
            "date_created": dict(),
            "default_password": dict(),
            "disk": dict(),
            "gateway_v4": dict(key='v4_gateway'),
            "internal_ip": dict(),
            "kvm_url": dict(),
            "label": dict(key='name'),
            "location": dict(key='region'),
            "main_ip": dict(key='v4_main_ip'),
            "netmask_v4": dict(key='v4_netmask'),
            "os": dict(),
            "pending_charges": dict(convert_to='float'),
            "power_status": dict(),
            "ram": dict(),
            "server_state": dict(),
            "status": dict(),
            "tag": dict(),
            "v6_main_ip": dict(),
            "v6_network": dict(),
            "v6_network_size": dict(),
            "v6_networks": dict(),
            "vcpu_count": dict(convert_to='int'),
        }

    def _get_application_name(self, application):
        if application == 0:
            return None

        return self.get_application(application, 'APPID').get('name')

    def _get_firewallgroup_name(self, firewallgroup):
        if firewallgroup == 0:
            return None

        return self.get_firewallgroup(firewallgroup, 'FIREWALLGROUPID').get('description')

    def _get_plan_name(self, plan):
        return self.get_plan(plan, 'VPSPLANID').get('name')

    def get_servers(self):
        return self.api_query(path="/v1/server/list")


def parse_servers_list(servers_list):
    return [server for id, server in servers_list.items()]


def main():
    argument_spec = vultr_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    server_facts = AnsibleVultrServerFacts(module)
    result = server_facts.get_result(parse_servers_list(server_facts.get_servers()))
    ansible_facts = {
        'vultr_server_facts': result['vultr_server_facts']
    }
    module.exit_json(ansible_facts=ansible_facts, **result)


if __name__ == '__main__':
    main()
