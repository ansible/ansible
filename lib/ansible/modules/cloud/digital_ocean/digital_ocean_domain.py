#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of Ansible
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
DOCUMENTATION = '''
---
module: digital_ocean_domain
short_description: Create/delete a DNS record in DigitalOcean
description:
     - Create/delete a DNS record in DigitalOcean.
version_added: "1.6"
options:
  state:
    description:
     - Indicate desired state of the target.
    default: present
    choices: ['present', 'absent']
  client_id:
     description:
     - DigitalOcean manager id.
  api_key:
    description:
     - DigitalOcean api key.
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
  - Two environment variables can be used, DO_CLIENT_ID and DO_API_KEY.
'''


EXAMPLES = '''
# Create a domain record

- digital_ocean_domain: >
      state=present
      name=my.digitalocean.domain
      ip=127.0.0.1

# Create a droplet and a corresponding domain record

- digital_ocean: >
      state=present
      name=test_droplet
      size_id=1
      region_id=2
      image_id=3
  register: test_droplet

- digital_ocean_domain: >
      state=present
      name={{ test_droplet.droplet.name }}.my.domain
      ip={{ test_droplet.droplet.ip_address }}
'''

import sys
import os
import time

try:
    from dopy.manager import DoError, DoManager
except ImportError as e:
    print "failed=True msg='dopy required for this module'"
    sys.exit(1)

class TimeoutError(DoError):
    def __init__(self, msg, id):
        super(TimeoutError, self).__init__(msg)
        self.id = id

class JsonfyMixIn(object):
    def to_json(self):
        return self.__dict__

class DomainRecord(JsonfyMixIn):
    manager = None

    def __init__(self, json):
        self.__dict__.update(json)
    update_attr = __init__

    def update(self, data = None, record_type = None):
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
        self.manager.destroy_domain(self.id)

    def records(self):
        json = self.manager.all_domain_records(self.id)
        return map(DomainRecord, json)

    @classmethod
    def add(cls, name, ip):
        json = cls.manager.new_domain(name, ip)
        return cls(json)

    @classmethod
    def setup(cls, client_id, api_key):
        cls.manager = DoManager(client_id, api_key)
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
        # params['client_id'] will be None even if client_id is not passed in
        client_id = module.params['client_id'] or os.environ['DO_CLIENT_ID']
        api_key = module.params['api_key'] or os.environ['DO_API_KEY']
    except KeyError, e:
        module.fail_json(msg='Unable to load %s' % e.message)

    changed = True
    state = module.params['state']

    Domain.setup(client_id, api_key)
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
                if record.name == "@":
                    at_record = record

            if not at_record.data == getkeyordie("ip"):
                record.update(data=getkeyordie("ip"), record_type='A')
                module.exit_json(changed=True, domain=Domain.find(id=record.domain_id).to_json())

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
        argument_spec = dict(
            state = dict(choices=['present', 'absent'], default='present'),
            client_id = dict(aliases=['CLIENT_ID'], no_log=True),
            api_key = dict(aliases=['API_KEY'], no_log=True),
            name = dict(type='str'),
            id = dict(aliases=['droplet_id'], type='int'),
            ip = dict(type='str'),
        ),
        required_one_of = (
            ['id', 'name'],
        ),
    )

    try:
        core(module)
    except TimeoutError as e:
        module.fail_json(msg=str(e), id=e.id)
    except (DoError, Exception) as e:
        module.fail_json(msg=str(e))

# import module snippets
from ansible.module_utils.basic import *

main()
