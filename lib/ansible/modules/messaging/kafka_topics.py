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
---
module: kafka_topics
author: "Guillaume Delpierre (@gdelpierre)"
version_added: "2.4"
short_description: Deal with kafka topics.
description:
    - "Alter/Create/Delete kafka topics"
requirements:
    - "kafka-topics.sh"
options:
    action:
        required: False
        default: list
        choices: ['list', 'describe', 'alter', 'create', 'delete']
        type: str
        description:
            - Specifies the action we want to perform.
    topic:
        required: False
        type: list
        description:
            - The topic to be create, alter or describe (single).
            The topics to be describe or list (multiple).
    config:
        required: False
        type: dict
        description:
            - A topic configuration override for the topic being created.
    zookeeper:
        required: True
        type: list
        description:
            - The connection string for the zookeeper connection. 
    replication_factor:
        required: False
        type: int
        description:
            -  The replication factor for each partition in the topic being created.
    partitions:
        required: False
        type: int
        description:
            - The number of partitions for the topic being created or altered.
    kafka_path:
        required: False
        default: '/opt/kafka'
        type: path
        description:
            - Kafka path.
    jaas_auth_file:
        required: False
        type: str
        description:
            - JAAS authentification file (needed for alter/create/delete actions).
'''

EXAMPLES = '''
name: 'list all topic'
kafka_topics:
  zookeeper:
    - zookeeper1.foo.bar:2181
    - zookeeper2.foo.bar:2181

name: 'list specific topic'
kafka_topics:
  topic: 'foobar'
  zookeeper:
    - zookeeper1.foo.bar:2181
    - zookeeper2.foo.bar:2181

name: 'Create topic foobar'
kafka_topics:
  action: 'create'
  topic: 'foobar'
  config:
    cleanup.policy: 'delete'
    compression.type: 'gzip'
  partitions: 2
  replication_factor: 1
  kafka_path: '/opt/kafka/kafka_2.11-0.10.1.1'
  jaas_auth_file: 'jaas-kafka.conf'
  zookeeper:
    - zookeeper1.foo.bar:2181
    - zookeeper2.foo.bar:2181

name: 'describe specific topic foobar'
kafka_topics:
  action: 'describe'
  topic: 'foobar'
  zookeeper:
    - zookeeper1.foo.bar:2181
    - zookeeper2.foo.bar:2181

name: 'alter partitions for topic foobar'
kafka_topics:
  action: 'alter'
  topic: 'foobar'
  partitions: 3
  jaas_auth_file: 'jaas-kafka.conf'
  zookeeper:
    - zookeeper1.foo.bar:2181
    - zookeeper2.foo.bar:2181

name: 'delete topic foobar'
kafka_topics:
  action: 'delete'
  topic: 'foobar'
  jaas_auth_file: 'jaas-kafka.conf'
  zookeeper:
    - zookeeper1.foo.bar:2181
    - zookeeper2.foo.bar:2181
'''

RETURN = '''
stdout:
  description: Output from stdout of kafka-topics command after execution of given command.
  returned: success
  type: string
  sample: ""

stdout_lines:
  description: kafka-topics command execution return value
  returned: always
  type: list
  sample:

stderr:
  description: kafka-topics command execution return value
  returned: failed
  type: string
  sample: "[2017-07-11 14:46:04,092] ERROR org.apache.kafka.common.errors.InvalidTopicException: topic name [foobar] is illegal, contains a character other than ASCII alphanumerics, '.', '_' and '-'\n (kafka.admin.TopicCommand$)\n"

rc:
  description: kafka-topics command execution return value
  returned: always
  type: int
  sample: 0

cmd:
  description: Executed command to get action done
  returned: success
  type: string
  sample: ""
'''

import os.path

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils._text import to_native

class KafkaError(Exception):
    pass
 
class KafkaTopics(object):

    def __init__(self, module):
        self.authentification = module.params['kafka_path'] + \
                                    '/config/' + module.params['jaas_auth_file']
        self.config = module.params['config']
        self.partitions = module.params['partitions']
        self.replication_factor = module.params['replication_factor']
        self.topic = module.params['topic']
        self.zookeeper  = ','.join(module.params['zookeeper'])

        self.executable = module.params['kafka_path'] + '/bin/kafka-topics.sh'
        self.kafka_env_opts = '-Djava.security.auth.login.config=' + \
                                self.authentification
        self.module = module

    def get(self):
        ''' List kafka topics. '''
        if self.topic:
            # list supports multiple topics
            topics = ','.join(self.topic)
            cmd = '%s --list --zookeeper %s --topic %s' % (self.executable,
                                                            self.zookeeper,
                                                            topics)
        else:
            cmd = "%s --list --zookeeper %s" % (self.executable, self.zookeeper)

        try:
            return self.module.run_command(cmd)

        except:
            e = get_exception()
            raise KafkaError(e)

    def describe(self):
        ''' Describe kafka topics. '''
        if self.topic:
            # describe supports multiple topics
            topics = ','.join(self.topic)
            cmd = '%s --describe --zookeeper %s --topic %s' % (self.executable,
                                                                self.zookeeper,
                                                                topics)
        else:
            cmd = '%s --describe --zookeeper %s' % (self.executable, self.zookeeper)

        try:
            return self.module.run_command(cmd)

        except:
            e = get_exception()
            raise KafkaError(e)

    def alter(self):
        ''' alter kafka topics. '''
        cmd_get_partitions = self.describe()
        # For a specific topic, we want the PartitionCount value.
        get_partitions = (cmd_get_partitions[1]
                        .splitlines()[0]
                        .split('\t')[1]
                        .split(':')[1]
        )
        # alter supports only 1 topic
        if len(self.topic) > 1:
                msg = 'alter action supports only 1 topic'
                return self.module.fail_json(msg)
        else:
            topic = ''.join(self.topic)
            cmd = ('%s --alter --if-exists --zookeeper %s '
                    '--partitions %s --topic %s') % (self.executable, self.zookeeper,
                                                        self.partitions, topic)

        try:
            env = { 'KAFKA_OPTS': self.kafka_env_opts }
            if int(get_partitions) < int(self.partitions):
                return self.module.run_command(cmd, environ_update=env)
            else:
                err_msg="""
                The number of partitions for a topic can only be increased.
                """
                return self.module.fail_json(msg=to_native(err_msg))

        except:
            e = get_exception()
            raise KafkaError(e)

    def create(self):
        ''' Create new kafka topic. '''
        # create action supports only 1 topic
        if len(self.topic) > 1:
                msg = 'alter action supports only 1 topic'
                return self.module.fail_json(msg)
        else:
            topic = ''.join(self.topic)
            if self.config:
                config = ' --config '.join("%s=%r" % (k, v) for (k,v) in self.config.iteritems())
                cmd = ('%s --create --if-not-exists --zookeeper %s '
                        '--replication-factor %s --partitions %s '
                        '--topic %s --config %s') % (self.executable,
                                                        self.zookeeper,
                                                        self.replication_factor,
                                                        self.partitions,
                                                        topic,
                                                        config)

            else:
                cmd = ('%s --create --if-not-exists --zookeeper %s '
                        '--replication-factor %s --partitions %s '
                        '--topic') % (self.executable, self.zookeeper,
                                       self.replication_factor, self.partitions,
                                        topic)

        try:
            env = { 'KAFKA_OPTS': self.kafka_env_opts }
            return self.module.run_command(cmd, environ_update=env)

        except:
            e = get_exception()
            raise KafkaError(e)

    def delete(self):
        ''' Delete a kafka topic. '''
        # create action supports only 1 topic
        if len(self.topic) > 1:
                msg = 'alter action supports only 1 topic'
                return self.module.fail_json(msg)
        else:
            topic = ''.join(self.topic)
            cmd = ('%s --delete --zookeeper %s '
                    '--topic %s --if-exists' ) % (self.executable, self.zookeeper,
                                                    topic)

        try:
            env = { 'KAFKA_OPTS': self.kafka_env_opts }
            return self.module.run_command(cmd, environ_update=env)

        except:
            e = get_exception()
            raise KafkaError(e)

def main():
    argument_spec = dict(
        action = dict(required=False, default='list',
                        choices=['list', 'describe', 'alter', 'create', 'delete'],
                        type='str'),
        topic = dict(required=False, type='list'),
        config = dict(required=False, type='dict'),
        zookeeper = dict(required=True, type='list'),
        replication_factor = dict(required=False, type='int'),
        partitions = dict(required=False, type='int'),
        kafka_path = dict(required=False, default='/opt/kafka',
                                type='path'),
        jaas_auth_file = dict(required=False, default='jaas.conf', type='str'),
    )

    required_if = [
        ['action', 'alter',
            [ 'topic', 'partitions', 'jaas_auth_file' ]
        ],
        ['action', 'create',
            [ 'topic', 'replication_factor', 'partitions', 'jaas_auth_file' ]
        ],
        ['action', 'delete',
            [ 'topic', 'jaas_auth_file' ]
        ],
    ]

    module = AnsibleModule(
        argument_spec = argument_spec,
        required_if = required_if,
        supports_check_mode = True,
    )

    kafka_bin = module.params['kafka_path'] + '/bin/kafka-topics.sh'
    is_kafka_bin = os.path.isfile(kafka_bin)

    if not is_kafka_bin:
        module.fail_json(msg='%s not found.' % (kafka_bin))

    if module.params['action'] in ['alter', 'create', 'delete']:
        jaas_auth_file = module.params['kafka_path'] + \
                            '/config/' + module.params['jaas_auth_file']
        is_jaas_auth_file = os.path.isfile(jaas_auth_file)
        if not is_jaas_auth_file:
           module.fail_json(msg='%s not found.' % (jaas_auth_file))

    try:
        kt = KafkaTopics(module)

        action = module.params['action']
        if not module.check_mode:
            if module.params['action'] == 'list':
                (rc, out, err) = kt.get()
            else:
                (rc, out, err) = getattr(kt, action)()

            result = {
                    'stdout': out,
                    'stdout_lines': out.splitlines(),
                    'stderr': err,
                    'rc': rc,
            }
            
    except KafkaError as e:
        module.fail_json(msg=to_native(e))

    module.exit_json(**result)

if __name__ == '__main__':
    main()
