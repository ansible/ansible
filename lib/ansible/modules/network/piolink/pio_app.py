#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Piolink Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: pio_app
short_description: Configuring WEBFRONT-K Applications
description:
   - You can manage the WEBFRONT-K applications.
version_added: 2.9
options:
  host:
    description:
      - Enter the IPv4 address of the WEBFRONT-K.
    required: True
  port:
    description:
      - Enter the port number of the WEBFRONT-K.
    required: True
  username:
    description:
      - Enter the User ID of the WEBFRONT-K. The ID must have permissions for the WEBFRONT-K.
    required: True
  password:
    description:
      - Enter the user's password.
    required: True
  app_name:
    description:
      - Enter the application name. "Application" means the applications provided by the WEBFRONT-K.
    required: True
  app_ip_list:
    description:
      - Enter the lists of IP addresses of the WEBFRONT-K application.
    type: list
    suboptions:
      app_ip:
        description:
          - Enter the IP addresses of the WEBFRONT-K application.
      app_port:
        description:
          - Enter the port numbers of the WEBFRONT-K application.
  app_domain_list:
    description:
      - Enter the lists of the domain names of the WEBFRONT-K application.
    type: list
    suboptions:
      app_domain:
        description:
          - Enter the domain names of the WEBFRONT-K application.
author: Piolink
'''

EXAMPLES = r'''
- name: Set App Config
  pio_app:
     host: 10.10.10.10
     port: 80
     username: admin
     password: secret
     app_name: pio_app_test
     app_ip_list:
        - app_ip: 1.1.1.1
        - app_port: 80
        - app_ip: 2.2.2.2
        - app_port: 80
     app_domain_list:
        - app_domain: 1.1.1.1
        - app_domain: 2.2.2.2
'''

RETURN = r'''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.piolink.prest_utils import PrestUtils
from ansible.module_utils.network.piolink.prest_module import CMD_APP_TYPE

app_ip_entry = dict(
    app_ip=dict(type='str'),
    app_port=dict(type='str'),
)

app_domain_entry = dict(
    app_domain=dict(type='str'),
)

module_args = dict(
    host=dict(type='str', required=True),
    port=dict(type='str', required=True),
    username=dict(type='str', required=True),
    password=dict(type='str', required=True, no_log=True),
    app_name=dict(type='str', required=True),
    app_ip_list=dict(type='list', elements='dict', options=app_ip_entry),
    app_domain_list=dict(type='list', elements='dict', options=app_domain_entry),
)


class PioApp(PrestUtils):
    def __init__(self, module):
        super(PioApp, self).__init__(module)

    def validate_ip_port(self, app_ip_entry):
        if self.validate_ip(app_ip_entry['app_ip']) is False:
            self.module.fail_json(msg="Invalid APP_IP: %s" % app_ip_entry['app_ip'])
        if self.validate_port(app_ip_entry['app_port']) is False:
            self.module.fail_json(msg="Invalid APP_Port: %s(range: 1~65535)"
                                  % app_ip_entry['app_port'])

    def set_app_iplist(self, app_id):
        url = self.set_url(CMD_APP_TYPE, 'app-gen', 'ip-list', app_id, None)

        for ip_entry in self.module.params['app_ip_list']:
            self.validate_ip_port(ip_entry)
            app_ip = self.get_entry(url, 'ip', ip_entry['app_ip'],
                                    'ip_list', 'ip_entry')
            if app_ip is not None:
                if app_ip['port'] == ip_entry['port']:
                    continue

            body = {'ip': ip_entry['app_ip'], 'port': ip_entry['app_port']}
            self.resp = self.post(url, body)

    def set_app_domainlist(self, app_id):
        url = self.set_url(CMD_APP_TYPE, 'app-gen', 'domain-list',
                           app_id, None)
        for domain_entry in self.module.params['app_domain_list']:
            app_domain = self.get_entry(url, 'domain', domain_entry['app_domain'],
                                        'domain_list', 'domain_entry')
            if app_domain is not None:
                continue

            body = {'domain': domain_entry['app_domain']}
            self.resp = self.post(url, body)

    def run(self):
        if self.module.check_mode:
            return self.result

        app_id = self.get_app_id()
        self.set_app_iplist(app_id)
        self.set_app_domainlist(app_id)


def main():
    module = AnsibleModule(module_args, supports_check_mode=True)
    app = PioApp(module)
    app.init_args()
    app.run()
    app.set_result()


if __name__ == '__main__':
    main()
