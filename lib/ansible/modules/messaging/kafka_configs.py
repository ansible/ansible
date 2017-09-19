#!/usr/bin/python
# Copyright (c) 2017 Guillaume Delpierre <gde@llew.me>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: kafka_configs
author: "Guillaume Delpierre (@gdelpierre)"
version_added: "2.5"

short_description: Manage entity configs.
description:
    - 'Add/Remove entity config for a topic, client, user or broker'
requirements:
    - 'kafka >= 2.11-0.10'
options:
    configs:
        description:
            - Key / Value (str) pairs of configs.
    describe:
        description:
            - List configs for the given entity.
    entity_default:
        description:
            - Default entity name for clients/users.
    entity_name:
        description:
            - Name of entity.
    entity_type:
        required: True
        description:
            - Type of entity.
    executable:
        description:
            - Kafka executable path if not in your current PATH or if it name differs.
    zookeeper:
        required: True
        description:
            - The connection string for the zookeeper connection.
              Multiple connection strings are allowed.
'''

EXAMPLES = '''
name: 'list config'
kafka_configs:
  entity_type: 'topics'
  describe: True
  zookeeper:
    - foo.baz.org:2181
    - bar.baz.org:2181

# If you have JAAS authentification,
# use environment variable
name: 'Manage config'
environment:
  KAFKA_OPTS: '-Djava.security.auth.login.config=/etc/kafka/jaas.conf'
kafka_configs:
  entity_name: 'chocolatine'
  entity_type: 'topics'
  configs:
    cleanup.policy: 'delete'
    compression.type: 'gzip'
    flush.ms: '234928'
  zookeeper:
    - foo.baz.org:2181
    - bar.baz.org:2181
'''

RETURN = '''
failed:
  description: Command execution return bool.
  returned: always
  type: bool
  sample: False

stdout:
  description: Output from stdout after execution
  returned: success or changed
  type: string
  sample: "Configs for topic 'wassingue' are cleanup.policy=delete,compression.type=gzip\\\\n"

msg:
  description: Output from stderr
  returned: failed
  type: string
  sample: "Error while executing config command Unknown Log configuration producer_byte_rate.\\\\n"
'''

import re
import os

from ansible.module_utils.basic import AnsibleModule, is_executable
from ansible.module_utils._text import to_native


class KafkaError(Exception):
    pass


class KafkaConfigs(object):

    def __init__(self, module):

        entity = {
            '--entity-default': module.params['entity_default'],
            '--entity-name': module.params['entity_name'],
            '--entity-type': module.params['entity_type'],
        }
        self.entity_join = ''.join(" %s %r" % (key, value) for key, value
                                   in entity.items() if value)

        self.msg = " entity: %s '%s'" % (module.params['entity_type'],
                                         module.params['entity_name'])

        self.configs = module.params['configs']
        self.zookeeper = ','.join(module.params['zookeeper'])

        self.executable = module.params['executable'] or module.get_bin_path('kafka-configs', True)

        self.module = module

    def manage_configs(self):
        ''' Alter (add or remove configs) for the entity. '''

        changed = False
        rc = 0
        msg = "Nothing to do for config" + self.msg

        try:

            # we get the configs.
            cmd_desc = '%s --describe --zookeeper %s %s' % (self.executable,
                                                            self.zookeeper,
                                                            self.entity_join)

            (_, out, _) = self.module.run_command(cmd_desc)

            # we build a dict of in place configs.
            configs_present = {}

            for line in out.splitlines():
                if 'are' not in line.split()[-1]:
                    configs_present = dict(
                        elmt.split('=') for elmt in line.split()[-1].split(',')
                    )

            # key/value for adding
            # only key to delete
            configs_to_add = {}
            configs_to_del = []

            # key to add and/or
            # key's value to update
            if self.configs.keys():
                for key in self.configs.keys():
                    if (key not in configs_present or
                            (key in configs_present and
                             configs_present[key] != self.configs[key])):

                        configs_to_add[key] = self.configs[key]

            # key to delete
            if configs_present.keys():
                for key in configs_present.keys():
                    if key not in self.configs:

                        configs_to_del.append(key)

            if configs_to_add:
                configs = ''
                for key, value in configs_to_add.items():
                    if configs:
                        configs += ','
                    configs += ''.join("%s=%r" % (key, value))

                cmd_add = ('%s --alter --zookeeper %s %s '
                           '--add-config %s') % (self.executable,
                                                 self.zookeeper,
                                                 self.entity_join,
                                                 configs)

            if configs_to_del:
                cmd_del = ('%s --alter --zookeeper %s %s '
                           '--delete-config %s') % (self.executable,
                                                    self.zookeeper,
                                                    self.entity_join,
                                                    ','.join(configs_to_del))

            output = ()

            if configs_to_add:
                (_, out_add, _) = self.module.run_command(cmd_add)
                if re.search('^Error while executing', out_add):
                    self.module.fail_json(msg=out_add)

                changed = True
                msg = "Updated config for" + self.msg

            if configs_to_del:
                (_, out_del, _) = self.module.run_command(cmd_del)

                changed = True
                msg = "Updated config for" + self.msg

            return (rc, msg, changed)

        except KafkaError as exc:
            self.module.fail_json(msg=to_native(exc))

    def describe(self):
        ''' List configs for the given entity. '''

        cmd = '%s --describe --zookeeper %s %s' % (self.executable,
                                                   self.zookeeper,
                                                   self.entity_join)

        return self.module.run_command(cmd)


def main():
    argument_spec = dict(
        describe=dict(default=False, type='bool'),
        configs=dict(type='dict'),
        entity_default=dict(type='str'),
        entity_name=dict(type='str'),
        entity_type=dict(required=True, type='str'),
        zookeeper=dict(required=True, type='list'),

        executable=dict(type='path'),
    )

    required_if = [
        ['configs', True, ['entity_name', 'entity_type']],
    ]

    required_one_of = [
        ['describe', 'configs'],
    ]

    mutually_exclusive = [
        ['describe', 'configs'],
    ]

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=required_if,
        required_one_of=required_one_of,
        mutually_exclusive=mutually_exclusive,
    )

    changed = False
    failed = False
    result = {}

    if not module.get_bin_path('kafka-configs') and module.params['executable'] is None:
        module.fail_json(msg='Executable not provided.')
    if module.params['executable'] is not None and not os.path.isfile(module.params['executable']):
        module.fail_json(msg='%s not found.' % (module.params['executable']))
    if not is_executable(module.params['executable']):
        module.fail_json(msg='%s not executable.' % (module.params['executable']))

    try:
        kc = KafkaConfigs(module)

        if module.params['describe']:
            (rc, out, err) = kc.describe()
        else:
            (rc, out, changed) = kc.manage_configs()

        result = {
            'failed': failed,
            'changed': changed,
        }

        if rc != 0:
            failed = True
        if out:
            result['stdout'] = out
        try:
            if err:
                result['msg'] = err
        except NameError:
            pass

    except KafkaError as exc:
        module.fail_json(msg=to_native(exc))

    module.exit_json(**result)

if __name__ == '__main__':
    main()
