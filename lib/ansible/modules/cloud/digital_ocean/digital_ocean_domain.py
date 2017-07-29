#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: digital_ocean_domain
short_description: Create/delete a DNS record in DigitalOcean
description:
     - Create/delete a DNS record in DigitalOcean.
version_added: "1.6"
author: "Michael Gregson (@mgregson)"
options:
  state:
    description:
     - Indicate desired state of the target.
    default: present
    choices: ['present', 'absent']
  api_token:
    description:
     - DigitalOcean api token.
    version_added: "1.9.5"
  id:
    description:
     - Numeric, the droplet id you want to operate on.
  name:
    description:
     - String, this is the name of the droplet - must be formatted by hostname rules, or the name of a SSH key, or the name of a domain.
  ip:
    description:
     - The IP address to point a domain at.

notes:
  - Two environment variables can be used, DO_API_KEY and DO_API_TOKEN. They both refer to the v2 token.
  - As of Ansible 1.9.5 and 2.0, Version 2 of the DigitalOcean API is used, this removes C(client_id) and C(api_key) options in favor of C(api_token).
  - If you are running Ansible 1.9.4 or earlier you might not be able to use the included version of this module as the API version used has been retired.

requirements:
  - "python >= 2.6"
  - dopy
'''


EXAMPLES = '''
# Create a domain record

- digital_ocean_domain:
    state: present
    name: my.digitalocean.domain
    ip: 127.0.0.1

# Create a droplet and a corresponding domain record

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

import os
import traceback

try:
    from dopy.manager import DoError, DoManager
    HAS_DOPY = True
except ImportError as e:
    HAS_DOPY = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


class JsonfyMixIn(object):

    def to_json(self):
        return self.__dict__


class DomainRecord(JsonfyMixIn):
    manager = None

    def __init__(self, json):
        self.__dict__.update(json)
    update_attr = __init__

    def update(self, data=None, record_type=None):
        json = self.manager.edit_domain_record(self.domain_id,
                                               self.id,
                                               record_type if record_type is not None else self.record_type,
                                               data if data is not None else self.data)
        self.__dict__.update(json)
        return self

    def destroy(self):
        json = self.manager.destroy_domain_record(self.domain_id, self.id)
        return json


class Domain(JsonfyMixIn):
    manager = None

    def __init__(self, domain_json):
        self.__dict__.update(domain_json)

    def destroy(self):
        self.manager.destroy_domain(self.name)

    def records(self):
        json = self.manager.all_domain_records(self.name)
        return map(DomainRecord, json)

    @classmethod
    def add(cls, name, ip):
        json = cls.manager.new_domain(name, ip)
        return cls(json)

    @classmethod
    def setup(cls, api_token):
        cls.manager = DoManager(None, api_token, api_version=2)
        DomainRecord.manager = cls.manager

    @classmethod
    def list_all(cls):
        domains = cls.manager.all_domains()
        return map(cls, domains)

    @classmethod
    def find(cls, name=None, id=None):
        if name is None and id is None:
            return False

        domains = Domain.list_all()

        if id is not None:
            for domain in domains:
                if domain.id == id:
                    return domain

        if name is not None:
            for domain in domains:
                if domain.name == name:
                    return domain

        return False


def core(module):
    def getkeyordie(k):
        v = module.params[k]
        if v is None:
            module.fail_json(msg='Unable to load %s' % k)
        return v

    try:
        api_token = module.params['api_token'] or os.environ['DO_API_TOKEN'] or os.environ['DO_API_KEY']
    except KeyError as e:
        module.fail_json(msg='Unable to load %s' % e.message)

    state = module.params['state']

    Domain.setup(api_token)
    if state in ('present'):
        domain = Domain.find(id=module.params["id"])

        if not domain:
            domain = Domain.find(name=getkeyordie("name"))

        if not domain:
            domain = Domain.add(getkeyordie("name"),
                                getkeyordie("ip"))
            module.exit_json(changed=True, domain=domain.to_json())
        else:
            records = domain.records()
            at_record = None
            for record in records:
                if record.name == "@" and record.type == 'A':
                    at_record = record

            if not at_record.data == getkeyordie("ip"):
                record.update(data=getkeyordie("ip"), record_type='A')
                module.exit_json(changed=True, domain=Domain.find(id=record.id).to_json())

        module.exit_json(changed=False, domain=domain.to_json())

    elif state in ('absent'):
        domain = None
        if "id" in module.params:
            domain = Domain.find(id=module.params["id"])

        if not domain and "name" in module.params:
            domain = Domain.find(name=module.params["name"])

        if not domain:
            module.exit_json(changed=False, msg="Domain not found.")

        event_json = domain.destroy()
        module.exit_json(changed=True, event=event_json)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['present', 'absent'], default='present'),
            api_token=dict(aliases=['API_TOKEN'], no_log=True),
            name=dict(type='str'),
            id=dict(aliases=['droplet_id'], type='int'),
            ip=dict(type='str'),
        ),
        required_one_of=(
            ['id', 'name'],
        ),
    )
    if not HAS_DOPY:
        module.fail_json(msg='dopy required for this module')

    try:
        core(module)
    except (DoError, Exception) as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
