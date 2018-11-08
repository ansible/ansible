#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: online_server_facts
short_description: Gather facts about Online servers.
description:
  - Gather facts about the servers.
  - U(https://www.online.net/en/dedicated-server)
version_added: "2.8"
author:
  - "Remy Leone (@sieben)"
extends_documentation_fragment: online
'''

EXAMPLES = r'''
- name: Gather Online server facts
  online_server_facts:
    api_token: '0d1627e8-bbf0-44c5-a46f-5c4d3aef033f'
'''

RETURN = r'''
---
online_server_facts:
  description: Response from Online API
  returned: success
  type: complex
  contains:
    "online_server_facts": [
        {
            "abuse": "abuse@example.com",
            "anti_ddos": false,
            "bmc": {
                "session_key": null
            },
            "boot_mode": "normal",
            "contacts": {
                "owner": "foobar",
                "tech": "foobar"
            },
            "disks": [
                {
                    "$ref": "/api/v1/server/hardware/disk/68452"
                },
                {
                    "$ref": "/api/v1/server/hardware/disk/68453"
                }
            ],
            "drive_arrays": [
                {
                    "disks": [
                        {
                            "$ref": "/api/v1/server/hardware/disk/68452"
                        },
                        {
                            "$ref": "/api/v1/server/hardware/disk/68453"
                        }
                    ],
                    "raid_controller": {
                        "$ref": "/api/v1/server/hardware/raidController/9910"
                    },
                    "raid_level": "RAID1"
                }
            ],
            "hardware_watch": true,
            "hostname": "sd-42",
            "id": 42,
            "ip": [
                {
                    "address": "195.154.172.149",
                    "mac": "28:92:4a:33:5e:c6",
                    "reverse": "195-154-172-149.rev.poneytelecom.eu.",
                    "switch_port_state": "up",
                    "type": "public"
                },
                {
                    "address": "10.90.53.212",
                    "mac": "28:92:4a:33:5e:c7",
                    "reverse": null,
                    "switch_port_state": "up",
                    "type": "private"
                }
            ],
            "last_reboot": "2018-08-23T08:32:03.000Z",
            "location": {
                "block": "A",
                "datacenter": "DC3",
                "position": 19,
                "rack": "A23",
                "room": "4 4-4"
            },
            "network": {
                "ip": [
                    "195.154.172.149"
                ],
                "ipfo": [],
                "private": [
                    "10.90.53.212"
                ]
            },
            "offer": "Pro-1-S-SATA",
            "os": {
                "name": "FreeBSD",
                "version": "11.1-RELEASE"
            },
            "power": "ON",
            "proactive_monitoring": false,
            "raid_controllers": [
                {
                    "$ref": "/api/v1/server/hardware/raidController/9910"
                }
            ],
            "support": "Basic service level"
        }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.online import (
    Online, OnlineException, online_argument_spec
)


class OnlineServerFacts(Online):

    def __init__(self, module):
        super(OnlineServerFacts, self).__init__(module)
        self.name = 'api/v1/server'

    def _get_server_detail(self, server_path):
        try:
            return self.get(path=server_path).json
        except OnlineException as exc:
            self.module.fail_json(msg="A problem occurred while fetching: %s (%s)" % (server_path, exc))

    def all_detailed_servers(self):
        servers_api_path = self.get_resources()

        server_data = (
            self._get_server_detail(server_api_path)
            for server_api_path in servers_api_path
        )

        return [s for s in server_data if s is not None]


def main():
    module = AnsibleModule(
        argument_spec=online_argument_spec(),
        supports_check_mode=True,
    )

    try:
        servers_facts = OnlineServerFacts(module).all_detailed_servers()
        module.exit_json(
            ansible_facts={'online_server_facts': servers_facts}
        )
    except OnlineException as exc:
        module.fail_json(msg=exc.message)


if __name__ == '__main__':
    main()
