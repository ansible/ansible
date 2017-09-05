#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: kafka_configs
author: "Guillaume Delpierre (@gdelpierre)"
version_added: "2.4"
short_description: Add/Remove entity config.
description:
    - 'Add/Remove entity config for a topic, client, user or broker'
requirements:
    - 'kafka-configs.sh'
options:
    add_configs:
        required: False
        type: dict
        description:
            - Key Value pairs of configs to add.
    del_configs:
        required: False
        type: list
        description:
            - Configs key to remove.
    describe:
        required: False
        type: bool
        default: False
        choices: [True, False]
        description:
            - List configs for the given entity.
    entity_default:
        required: False
        type: str
        description:
            - Default entity name for clients/users.
    entity_name:
        required: False
        type: str
        description:
            - Name of entity.
    entity_type:
        required: True
        type: str
        description:
            - Type of entity.
    jaas_auth_file:
        required: False
        type: str
        description:
            - JAAS authentification file.
    kafka_path:
        required: False
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

import os.path

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils._text import to_native

class KafkaError(Exception):
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

        authentification = self.module.params['kafka_path'] + \
                            '/config/' + self.module.params['jaas_auth_file']
        kafka_env_opts = '-Djava.security.auth.login.config=' + \
                                authentification
   
        entity = {
                '--entity-default': self.ent_def,
                '--entity-name': self.ent_name,
                '--entity-type': self.ent_type,
        }
        entity_join = ''.join(" %s %r" % (k, v) for k,v in entity.iteritems() if v)

        if self.add_configs:
            configs = ''
            for k,v in self.add_configs.iteritems():
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
        if self.del_configs:
            cmd = ('%s --alter --zookeeper %s %s '
                    '--delete-config %s') % (self.executable,
                                            self.zookeeper,
                                            entity_join,
                                            ','.join(self.del_configs))

        try:
            env = { 'KAFKA_OPTS': kafka_env_opts }
            return self.module.run_command(cmd, environ_update=env)

        except:
            e = get_exception()
            raise KafkaError(e)

    def describe(self):
        ''' List configs for the given entity. '''

        entity = {
                '--entity-default': self.ent_def,
                '--entity-name': self.ent_name,
                '--entity-type': self.ent_type,
        }
        entity_join = ''.join(" %s %r" % (k, v) for k,v in entity.iteritems() if v)

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

        except:
            e = get_exception()
            raise KafkaError(e)

def main():
    argument_spec = dict(
            describe=dict(required=False, 
                        choices=[True, False], type='bool'),
            add_configs=dict(required=False, type='dict'),
            del_configs=dict(required=False, type='list'),
            entity_default=dict(required=False, type='str'),
            entity_name=dict(required=False, type='str'),
            entity_type=dict(required=True, type='str'),
            zookeeper=dict(required=True, type='list'),

            jaas_auth_file = dict(required=False, type='str'),
            kafka_path = dict(required=False, default='/opt/kafka',
                                type='path'),

            pretty = dict(required=False, type='bool'),
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
        argument_spec = argument_spec,
        required_if = required_if,
        required_one_of = required_one_of,
        mutually_exclusive = mutually_exclusive,
        supports_check_mode = True,
    )

    kafka_bin = os.path.isfile(module.params['kafka_path'] + \
                    '/bin/kafka-configs.sh')

    if not kafka_bin:
        module.fail_json(msg='%s not found.' % (kafka_bin))

    if module.params['jaas_auth_file']:
        jaas_auth_file = os.path.isfile(module.params['kafka_path'] + \
                            '/config/' + module.params['jaas_auth_file'])
        if not jaas_auth_file:
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
                }
            else:
                (rc, out, err) = kc.manage_configs()
                result = {
                        'stdout': out,
                        'stdout_lines': out.splitlines(),
                        'stderr_lines': err.splitlines(),
                        'rc': rc,
                }

    except KafkaError as e:
        module.fail_json(msg=to_native(e))

    module.exit_json(**result)

if __name__ == '__main__':
    main()
