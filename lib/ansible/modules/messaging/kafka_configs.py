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

short_description: Add/Remove entity config.
description:
    - 'Add/Remove entity config for a topic, client, user or broker'
requirements:
    - 'kafka-configs.sh'
options:
    add_configs:
        type: dict
        description:
            - Key Value pairs of configs to add.
    del_configs:
        type: list
        description:
            - Configs key to remove.
    describe:
        type: bool
        default: False
        description:
            - List configs for the given entity.
    entity_default:
        type: str
        description:
            - Default entity name for clients/users.
    entity_name:
        type: str
        description:
            - Name of entity.
    entity_type:
        required: True
        type: str
        description:
            - Type of entity.
    jaas_auth_file:
        type: path
        description:
            - JAAS authentification path file.
    kafka_path:
        type: path
        description:
            - Kafka path.
    pretty:
        required:
        type:
        description:
            - Print a dict of the output.
    zookeeper:
        required: True
        type: list
        description:
            - The connection string for the zookeeper connection.
'''

EXAMPLES = '''
name: 'list config'
kafka_configs:
  kafka_path: '/opt/foobar/kafka'
  entity_type: 'topics'
  describe: True
  pretty: True
  zookeeper:
    - foo.baz.org:2181
    - bar.baz.org:2181

name: 'Add config'
kafka_configs:
  jaas_auth_file: 'jaas-kafka.conf'
  entity_name: 'chocolatine'
  entity_type: 'topics'
  add_configs:
    cleanup.policy: 'delete'
    compression.type: 'gzip'
  zookeeper:
    - foo.baz.org:2181
    - bar.baz.org:2181

name: 'Remove config'
kafka_configs:
  jaas_auth_file: 'jaas-kafka.conf'
  entity_name: 'chocolatine'
  entity_type: 'topics'
  del_configs:
    - cleanup.policy
    - compression.type
  zookeeper:
    - foo.baz.org:2181
    - bar.baz.org:2181
'''

RETURN = '''
'''

import re
import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.six import iteritems

class KafkaError(Exception):
    ''' '''
    pass


class KafkaConfigs(object):

    def __init__(self, module):

        self.add_configs = module.params['add_configs']
        self.del_configs = module.params['del_configs']
        self.ent_def = module.params['entity_default']
        self.ent_name = module.params['entity_name']
        self.ent_type = module.params['entity_type']
        self.pretty = module.params['pretty']
        self.zookeeper  = ','.join(module.params['zookeeper'])

        self.executable = module.params['kafka_path'] + '/bin/kafka-configs.sh'

        self.module = module

    def manage_configs(self):
        ''' Alter (add or remove configs) for the entity. '''

        if self.module.params['jaas_auth_file']:
            kafka_env_opts = '-Djava.security.auth.login.config=' + \
                self.module.params['jaas_auth_file']

        entity = {
                '--entity-default': self.ent_def,
                '--entity-name': self.ent_name,
                '--entity-type': self.ent_type,
        }
        entity_join = ''.join(" %s %r" % (k, v) for k, v in entity.iteritems() if v)

        if self.add_configs:
            configs = ''
            for k, v in self.add_configs.iteritems():
                if v:
                    if isinstance(v, list):
                        if configs:
                            configs += ','
                        configs += ''.join("%s=%r" % (k, ','.join(v)))
                    else:
                        if configs:
                            configs += ','
                        configs += ''.join("%s=%r" % (k, v))

            cmd = ('%s --alter --zookeeper %s %s '
                   '--add-config %s') % (self.executable,
                                         self.zookeeper,
                                         entity_join,
                                         configs)
        elif self.del_configs:
            cmd = ('%s --alter --zookeeper %s %s '
                   '--delete-config %s') % (self.executable,
                                            self.zookeeper,
                                            entity_join,
                                            ','.join(self.del_configs))
        else:
            msg = 'add/del action required at least one config to add/del'
            return self.module.fail_json(msg=msg)

        try:
            env = ''
            if self.module.params['jaas_auth_file']:
                env = {'KAFKA_OPTS': kafka_env_opts}

            return self.module.run_command(cmd, environ_update=env)

        except KafkaError as exc:
            self.module.fail_json(msg=to_native(exc))

    def describe(self):
        ''' List configs for the given entity. '''

        entity = {
            '--entity-default': self.ent_def,
            '--entity-name': self.ent_name,
            '--entity-type': self.ent_type,
        }
        entity_join = ''.join(" %s %r" % (k, v) for k, v in entity.iteritems() if v)

        try:
            cmd = '%s --describe --zookeeper %s %s' % (self.executable,
                                                       self.zookeeper,
                                                       entity_join)
            if self.pretty:
                (rc, out, err) = self.module.run_command(cmd)

                formatted = {}

                for line in out.splitlines():
                    if not 'are' in line.split()[-1]:
                        if len(line.split()[-1].split(',')) > 1:
                            formatted[line.split()[3].strip('\'')] = line.split()[-1].split(',')
                        else:
                            formatted[line.split()[3].strip('\'')] = line.split()[-1]
                    else:
                        formatted[line.split()[3].strip('\'')] = 'null'

                return (rc, formatted, err)

            return self.module.run_command(cmd)

        except KafkaError as exc:
            self.module.fail_json(msg=to_native(exc))


def main():
    argument_spec = dict(
        describe=dict(default=False, type='bool'),
        add_configs=dict(type='dict'),
        del_configs=dict(type='list'),
        entity_default=dict(type='str'),
        entity_name=dict(type='str'),
        entity_type=dict(required=True, type='str'),
        zookeeper=dict(required=True, type='list'),

        jaas_auth_file=dict(type='path'),
        kafka_path=dict(default='/opt/kafka',
                        type='path'),

        pretty=dict(default=False, type='bool'),
    )

    required_if = [
        ['add_configs', True, ['entity_name', 'entity_type']],
        ['add_configs', True, ['jaas_auth_file']],
        ['del_configs', True, ['jaas_auth_file']],
    ]

    required_one_of = [
        ['describe', 'add_configs', 'del_configs'],
    ]

    mutually_exclusive = [
        ['add_configs', 'del_configs', 'describe'],
    ]

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=required_if,
        required_one_of=required_one_of,
        mutually_exclusive=mutually_exclusive,
        supports_check_mode=True,
    )

    kafka_bin = os.path.isfile(module.params['kafka_path'] +
                               '/bin/kafka-configs.sh')
    jaas_auth_file = module.params['jaas_auth_file']

    changed = False

    if not kafka_bin:
        module.fail_json(msg='%s not found.' % (kafka_bin))

    if module.params['jaas_auth_file']:
        is_jaas_auth_file = os.path.isfile(jaas_auth_file)
        if not is_jaas_auth_file:
            module.fail_json(msg='%s not found.' % (jaas_auth_file))

    try:
        kc = KafkaConfigs(module)

        if not module.check_mode:
            if module.params['describe']:
                (rc, out, err) = kc.describe()
                result = {
                    'stdout': to_native(out),
                    'stderr_lines': err.splitlines(),
                    'rc': rc,
                    'changed': changed,
                }
            else:
                (rc, out, err) = kc.manage_configs()
                if re.search('^Updated config for entity:', out):
                    changed = True
                result = {
                    'stdout': out,
                    'stdout_lines': out.splitlines(),
                    'stderr_lines': err.splitlines(),
                    'rc': rc,
                    'changed': changed,
                }

    except KafkaError as e:
        module.fail_json(msg=to_native(e))

    module.exit_json(**result)

if __name__ == '__main__':
    main()
