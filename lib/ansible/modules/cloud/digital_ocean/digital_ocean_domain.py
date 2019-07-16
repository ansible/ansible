#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: digital_ocean_domain
short_description: Create/delete a DNS domain in DigitalOcean
description:
     - Create/delete a DNS domain in DigitalOcean.
version_added: "1.6"
author: "Michael Gregson (@mgregson)"
options:
  state:
    description:
     - Indicate desired state of the target.
    default: present
    choices: ['present', 'absent']
  id:
    description:
     - Numeric, the droplet id you want to operate on.
    aliases: ['droplet_id']
  name:
    description:
     - String, this is the name of the droplet - must be formatted by hostname rules, or the name of a SSH key, or the name of a domain.
  ip:
    description:
     - An 'A' record for '@' ($ORIGIN) will be created with the value 'ip'.  'ip' is an IP version 4 address.
extends_documentation_fragment: digital_ocean.documentation
notes:
  - Environment variables DO_OAUTH_TOKEN can be used for the oauth_token.
  - As of Ansible 1.9.5 and 2.0, Version 2 of the DigitalOcean API is used, this removes C(client_id) and C(api_key) options in favor of C(oauth_token).
  - If you are running Ansible 1.9.4 or earlier you might not be able to use the included version of this module as the API version used has been retired.

requirements:
  - "python >= 2.6"
'''


EXAMPLES = '''
# Create a domain

- digital_ocean_domain:
    state: present
    name: my.digitalocean.domain
    ip: 127.0.0.1

# Create a droplet and a corresponding domain

- digital_ocean:
    state: present
    name: test_droplet
    size_id: 1gb
    region_id: sgp1
    image_id: ubuntu-14-04-x64


  register: test_droplet

- digital_ocean_domain:
    state: present
    name: "{{ test_droplet.droplet.name }}.my.domain"
    ip: "{{ test_droplet.droplet.ip_address }}"

'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper
from ansible.module_utils._text import to_native


class DoManager(DigitalOceanHelper, object):
    def __init__(self, module):
        super(DoManager, self).__init__(module)
        self.domain_name = module.params.get('name', None)
        self.domain_ip = module.params.get('ip', None)
        self.domain_id = module.params.get('id', None)

    @staticmethod
    def jsonify(response):
        return response.status_code, response.json

    def all_domains(self):
        resp = self.get('domains/')
        return resp

    def find(self):
        if self.domain_name is None and self.domain_id is None:
            return False

        domains = self.all_domains()
        status, json = self.jsonify(domains)
        for domain in json['domains']:
            if domain['name'] == self.domain_name:
                return True
        return False

    def add(self):
        params = {'name': self.domain_name, 'ip_address': self.domain_ip}
        resp = self.post('domains/', data=params)
        status = resp.status_code
        json = resp.json
        if status == 201:
            return json['domain']
        else:
            return json

    def all_domain_records(self):
        resp = self.get('domains/%s/records/' % self.domain_name)
        return resp.json

    def domain_record(self):
        resp = self.get('domains/%s' % self.domain_name)
        status, json = self.jsonify(resp)
        return json

    def destroy_domain(self):
        resp = self.delete('domains/%s' % self.domain_name)
        status, json = self.jsonify(resp)
        if status == 204:
            return True
        else:
            return json

    def edit_domain_record(self, record):
        params = {'name': '@',
                  'data': self.module.params.get('ip')}
        resp = self.put('domains/%s/records/%s' % (self.domain_name, record['id']), data=params)
        status, json = self.jsonify(resp)

        return json['domain_record']

    def create_domain_record(self):
        params = {'name': '@',
                  'type': 'A',
                  'data': self.module.params.get('ip')}

        resp = self.post('domains/%s/records' % (self.domain_name), data=params)
        status, json = self.jsonify(resp)

        return json['domain_record']


def core(module):
    do_manager = DoManager(module)
    state = module.params.get('state')

    domain = do_manager.find()
    if state == 'present':
        if not domain:
            domain = do_manager.add()
            if 'message' in domain:
                module.fail_json(changed=False, msg=domain['message'])
            else:
                module.exit_json(changed=True, domain=domain)
        else:
            records = do_manager.all_domain_records()
            at_record = None
            for record in records['domain_records']:
                if record['name'] == "@" and record['type'] == 'A':
                    at_record = record

            if not at_record:
                do_manager.create_domain_record()
                module.exit_json(changed=True, domain=do_manager.find())
            elif not at_record['data'] == module.params.get('ip'):
                do_manager.edit_domain_record(at_record)
                module.exit_json(changed=True, domain=do_manager.find())
            else:
                module.exit_json(changed=False, domain=do_manager.domain_record())

    elif state == 'absent':
        if not domain:
            module.exit_json(changed=False, msg="Domain not found")
        else:
            delete_event = do_manager.destroy_domain()
            if not delete_event:
                module.fail_json(changed=False, msg=delete_event['message'])
            else:
                module.exit_json(changed=True, event=None)
        delete_event = do_manager.destroy_domain()
        module.exit_json(changed=delete_event)


def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    argument_spec.update(
        state=dict(choices=['present', 'absent'], default='present'),
        name=dict(type='str'),
        id=dict(aliases=['droplet_id'], type='int'),
        ip=dict(type='str')
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=(
            ['id', 'name'],
        ),
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
