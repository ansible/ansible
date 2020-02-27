#!/usr/bin/python

# Copyright: (c) 2016, Kamil Szczygiel <kamil.szczygiel () intel.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: influxdb_retention_policy
short_description: Manage InfluxDB retention policies
description:
    - Manage InfluxDB retention policies.
version_added: 2.1
author: "Kamil Szczygiel (@kamsz)"
requirements:
    - "python >= 2.6"
    - "influxdb >= 0.9"
    - requests
options:
    database_name:
        description:
            - Name of the database.
        required: true
        type: str
    policy_name:
        description:
            - Name of the retention policy.
        required: true
        type: str
    duration:
        description:
            - Determines how long InfluxDB should keep the data.
        required: true
        type: str
    replication:
        description:
            - Determines how many independent copies of each point are stored in the cluster.
        required: true
        type: int
    default:
        description:
            - Sets the retention policy as default retention policy.
        type: bool
extends_documentation_fragment: influxdb
'''

EXAMPLES = r'''
# Example influxdb_retention_policy command from Ansible Playbooks
- name: create 1 hour retention policy
  influxdb_retention_policy:
      hostname: "{{influxdb_ip_address}}"
      database_name: "{{influxdb_database_name}}"
      policy_name: test
      duration: 1h
      replication: 1
      ssl: yes
      validate_certs: yes

- name: create 1 day retention policy
  influxdb_retention_policy:
      hostname: "{{influxdb_ip_address}}"
      database_name: "{{influxdb_database_name}}"
      policy_name: test
      duration: 1d
      replication: 1

- name: create 1 week retention policy
  influxdb_retention_policy:
      hostname: "{{influxdb_ip_address}}"
      database_name: "{{influxdb_database_name}}"
      policy_name: test
      duration: 1w
      replication: 1

- name: create infinite retention policy
  influxdb_retention_policy:
      hostname: "{{influxdb_ip_address}}"
      database_name: "{{influxdb_database_name}}"
      policy_name: test
      duration: INF
      replication: 1
      ssl: no
      validate_certs: no
'''

RETURN = r'''
# only defaults
'''

import re

try:
    import requests.exceptions
    from influxdb import exceptions
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.influxdb import InfluxDb
from ansible.module_utils._text import to_native


def find_retention_policy(module, client):
    database_name = module.params['database_name']
    policy_name = module.params['policy_name']
    hostname = module.params['hostname']
    retention_policy = None

    try:
        retention_policies = client.get_list_retention_policies(database=database_name)
        for policy in retention_policies:
            if policy['name'] == policy_name:
                retention_policy = policy
                break
    except requests.exceptions.ConnectionError as e:
        module.fail_json(msg="Cannot connect to database %s on %s : %s" % (database_name, hostname, to_native(e)))
    return retention_policy


def create_retention_policy(module, client):
    database_name = module.params['database_name']
    policy_name = module.params['policy_name']
    duration = module.params['duration']
    replication = module.params['replication']
    default = module.params['default']

    if not module.check_mode:
        try:
            client.create_retention_policy(policy_name, duration, replication, database_name, default)
        except exceptions.InfluxDBClientError as e:
            module.fail_json(msg=e.content)
    module.exit_json(changed=True)


def alter_retention_policy(module, client, retention_policy):
    database_name = module.params['database_name']
    policy_name = module.params['policy_name']
    duration = module.params['duration']
    replication = module.params['replication']
    default = module.params['default']
    duration_regexp = re.compile(r'(\d+)([hdw]{1})|(^INF$){1}')
    changed = False

    duration_lookup = duration_regexp.search(duration)

    if duration_lookup.group(2) == 'h':
        influxdb_duration_format = '%s0m0s' % duration
    elif duration_lookup.group(2) == 'd':
        influxdb_duration_format = '%sh0m0s' % (int(duration_lookup.group(1)) * 24)
    elif duration_lookup.group(2) == 'w':
        influxdb_duration_format = '%sh0m0s' % (int(duration_lookup.group(1)) * 24 * 7)
    elif duration == 'INF':
        influxdb_duration_format = '0'

    if (not retention_policy['duration'] == influxdb_duration_format or
            not retention_policy['replicaN'] == int(replication) or
            not retention_policy['default'] == default):
        if not module.check_mode:
            try:
                client.alter_retention_policy(policy_name, database_name, duration, replication, default)
            except exceptions.InfluxDBClientError as e:
                module.fail_json(msg=e.content)
        changed = True
    module.exit_json(changed=changed)


def main():
    argument_spec = InfluxDb.influxdb_argument_spec()
    argument_spec.update(
        database_name=dict(required=True, type='str'),
        policy_name=dict(required=True, type='str'),
        duration=dict(required=True, type='str'),
        replication=dict(required=True, type='int'),
        default=dict(default=False, type='bool')
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    influxdb = InfluxDb(module)
    client = influxdb.connect_to_influxdb()

    retention_policy = find_retention_policy(module, client)

    if retention_policy:
        alter_retention_policy(module, client, retention_policy)
    else:
        create_retention_policy(module, client)


if __name__ == '__main__':
    main()
