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
version_added: "1.8"
options:
  state:
    description:
     - Indicate desired state of the target.
    default: present
    choices: ['present', 'absent']
  client_id:
     description:
     - Digital Ocean manager id.
  api_key:
    description:
     - Digital Ocean api key.
  domain:
    description:
     - Required, String, Domain Name (e.g. domain.com), specifies the domain
       for which to create a record.
  type:
    description:
     - Required, String, the type of record you would like to create. A, CNAME,
       NS, TXT, MX or SRV.
  data:
    description:
     - Required, String, this is the value of the record.
  name:
    description:
     - Optional, String, required for A, CNAME, TXT and SRV records.
  priority:
    description:
     - Optional, Integer, required for SRV and MX records.
  port:
    description:
     - Optional, Integer, required for SRV records.
  weight:
    description:
     - Optional, Integer, required for SRV records.

notes:
  - Two environment variables can be used, DO_CLIENT_ID and DO_API_KEY.
'''


EXAMPLES = '''
# Create a DNS record

- digital_ocean_domain: >
      state=present
      domain=digitalocean.example
      type="A"
      name=www
      ip=127.0.0.1

# Remove a DNS record

- digital_ocean_domain: >
      state=absent
      domain=digitalocean.example
      type="A"
      name=www
      ip=127.0.0.1


# Create a droplet and a corresponding DNS record

- digital_ocean: >
      state=present
      name=test_droplet
      size_id=1
      region_id=2
      image_id=3
  register: test_droplet

- digital_ocean_domain: >
      state=present
      domain=digitalocean.example
      type="A"
      name={{ test_droplet.droplet.name }}
      data={{ test_droplet.droplet.ip_address }}
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

    @classmethod
    def add(cls, domain_id, type, data, name=None,
            priority=None, port=None, weight=None):
        json = cls.manager.new_domain_record(domain_id, type, data, name,
                                             priority, port, weight)
        return cls(json)

    @classmethod
    def find(cls, domain_id, type, data, name, priority, port, weight):
        json = cls.manager.all_domain_records(domain_id)
        records = map(DomainRecord, json)

        for record in records:
            if (record.record_type == type and record.data == data
                and record.name == name and record.priority == priority
                and record.port == port and record.weight == weight):
                    return record

        return False

    def update(self, data=None, record_type=None):
        if not record_type:
            record_type = self.record_type
        data = data if data is not None else self.data
        json = self.manager.edit_domain_record(self.domain_id, self.id,
                                               new_type, data)
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

    def find_record(self, type, data, name,
                    priority=None, port=None, weight=None):
        return DomainRecord.find(self.id, type, data, name,
                                 priority, port, weight)

    def add_record(self, type, data, name, priority=None, port=None,
               weight=None):
        return DomainRecord.add(self.id, type, data, name, priority, port,
                    weight)

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
    domain_name = getkeyordie("domain")

    Domain.setup(client_id, api_key)
    domain = Domain.find(name=domain_name)

    if not domain:
        module.fail_json(msg='Domain not found %s' % domain_name)

    type = getkeyordie("type")
    data = module.params['data']
    name = module.params['name']
    priority = module.params['priority']
    port = module.params['port']
    weight = module.params['weight']

    record = domain.find_record(type, data, name, priority, port, weight)

    if state in ('present') and not record:
        record = domain.add_record(type, data, name, priority, port, weight)
        module.exit_json(changed=True, record=record.to_json())

    elif state in ('absent') and record:
        json = record.destroy()
        module.exit_json(changed=True, event=json)

    module.exit_json(changed=False, record=record.to_json())


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['present', 'absent'], default='present'),
            client_id=dict(aliases=['CLIENT_ID'], no_log=True),
            api_key=dict(aliases=['API_KEY'], no_log=True),
            domain=dict(type='str'),
            type=dict(choices=['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'SRV', 'NS'],
                      default='A'),
            name=dict(type='str'),
            data=dict(type='str'),
            priority=dict(type='int'),
            port=dict(type='int'),
            weight=dict(type='int'),
        )
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
