#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019 Jon, Alfaro (jon.alfaro@vorteil.io)
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: vorteil_get_sample_vcfg

short_description: Prints a sample vcfg json configuration

version_added: "2.10"

description:
    - Prints a sample vcfg configuration.
    - Please note this a sample configuration and will not work, it is to used as a reference.

options:
    format:
        description:
            - Structure type to print vcfg.
        required: false
        choices: ['json', 'toml']
        default: 'json'
        type: str

author:
    - Jon Alfaro (@jalfvort)

requirements: 
    - requests
    - toml
    - Vorteil >=3.0.6
'''

EXAMPLES = r'''
- name: print sample vcfg
  vorteil_get_sample_vcfg:
      format: "json"
'''

RETURN = r'''
results:
    description:
    - Prints sample vcfg in configured format
    returned: success
    type: str
    sample:
        {
            "response": "{{ json_vcfg_dump }}"
        }
'''

import traceback

from ansible.module_utils.basic import AnsibleModule

def main():

    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        format=dict(type='str', choices=['json','toml'], default='json')
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    jsonVCFG = { "json": """
    {
        "program": [
            {
            "binary": "/usr/bin/path",
            "args": "-jar myapp.jar",
            "env": [
                "HOME=/",
                "USER=root"
            ]
            }
        ],
        "network": [
            {
            "ip": "dhcp",
            "mask": "255.255.255.255",
            "gateway": "192.168.1.1",
            "tcp": [
                "8080"
            ],
            "mtu": 1500
            }
        ],
        "system": {
            "disk-cache": "64 MiB",
            "dns": [
            "8.8.8.8",
            "8.8.4.4"
            ],
            "hostname": "localhost",
            "max-fds": 1024,
            "output-mode": "standard",
            "output-format": "standard"
        },
        "info": {
            "name": "MyApp",
            "author": "Mr Smith",
            "summary": "MyApp that does stuff",
            "description": "# MyApp",
            "url": "vorteil.io",
            "date": "23 Apr 19 07:59 AEST",
            "version": "0289"
        },
        "vm": {
            "cpus": 1,
            "ram": "128 MiB",
            "inodes": 1024,
            "kernel": "1.0.0",
            "disk-size": "64 MiB"
        }
    }
    """}

    tomlVCFG = """
    [[program]]
        binary = "/usr/bin/path"
        args = "-jar myapp.jar"
        env = ["HOME=/", "USER=root"]

    [[network]]
        ip = "dhcp"
        mask = "255.255.255.255"
        gateway = "192.168.1.1"
        tcp = ["8080"]
        mtu = 1500

    [system]
        disk-cache = "64 MiB"
        dns = ["8.8.8.8", "8.8.4.4"]
        hostname = "localhost"
        max-fds = 1024
        output-mode = "standard"
        output-format = "standard"

    [info]
        name = "MyApp"
        author = "Mr Smith"
        summary = "MyApp that does stuff"
        description = "# MyApp"
        url = "vorteil.io"
        date = "23 Apr 19 07:59 AEST"
        version = "0289"

    [vm]
        cpus = 1
        ram = "128 MiB"
        inodes = 1024
        kernel = "1.0.0"
        disk-size = "64 MiB"
    """

    # set repo_cookie if repo_key is provided
    if module.params['format'] == "toml":
        module.exit_json(changed=False, response=tomlVCFG)
    elif module.params['format'] == "json":
        module.exit_json(changed=False, response=jsonVCFG)


if __name__ == '__main__':
    main()
