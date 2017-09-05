#!/usr/bin/python
# Copyright (c) 2017 Guillaume Delpierre <gde@llew.me>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# -*- coding: utf-8 -*-

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: kafka_topics
author: "Guillaume Delpierre (@gdelpierre)"
version_added: "2.5"
short_description: Deal with kafka topics.
description:
    - "Alter/Create/Delete kafka topics"
requirements:
    - "kafka-topics.sh"
options:
    action:
        default: list
        choices: ['list', 'describe', 'alter', 'create', 'delete']
        type: str
        description:
            - Specifies the action we want to perform.
    topic:
        type: list
        description:
            - The topic to be create, alter or describe (single).
              The topics to be describe or list (multiple).
    config:
        type: dict
        description:
            - A topic configuration override for the topic being created.
    zookeeper:
        required: True
        type: list
        description:
            - The connection string for the zookeeper connection. 
    replication_factor:
        type: int
        description:
            -  The replication factor for each partition in the topic being created.
    partitions:
        type: int
        description:
            - The number of partitions for the topic being created or altered.
    kafka_path:
        default: '/opt/kafka'
        type: path
        description:
            - Kafka path.
    jaas_auth_file:
        type: path
        description:
            - JAAS authentification path file.
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
  jaas_auth_file: '/opt/kafka/sec/jaas-kafka.conf'
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
  jaas_auth_file: '/opt/kafka/sec/jaas-kafka.conf'
  zookeeper:
    - zookeeper1.foo.bar:2181
    - zookeeper2.foo.bar:2181

name: 'delete topic foobar'
kafka_topics:
  action: 'delete'
  topic: 'foobar'
  jaas_auth_file: '/opt/kafka/sec/jaas-kafka.conf'
  zookeeper:
    - zookeeper1.foo.bar:2181
    - zookeeper2.foo.bar:2181
'''

RETURN = '''
stdout:
  description: Output from stdout of kafka-topics command after execution of given command.
  returned: success
  type: string
  sample: "Created topic raclette"

stdout_lines:
  description: kafka-topics command execution return value
  returned: always
  type: list
  sample: ["Created topic raclette"]

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
'''

import re
import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

class KafkaError(Exception):
    ''' '''
    pass
 
class KafkaTopics(object):

    def __init__(self, module):

        self.config = module.params['config']
        self.partitions = module.params['partitions']
        self.replication_factor = module.params['replication_factor']
        self.topic = module.params['topic']
        self.zookeeper  = ','.join(module.params['zookeeper'])

        self.kafka_path = module.params['kafka_path']
        self.executable = self.kafka_path + '/bin/kafka-topics.sh'

        if module.params['jaas_auth_file']:
            self.jaas_auth_file = module.params['jaas_auth_file']
            self.kafka_env_opts = '-Djava.security.auth.login.config=' + \
                self.jaas_auth_file

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
            cmd = "%s --list --zookeeper %s" % (self.executable,
                                                self.zookeeper)

        try:
            return self.module.run_command(cmd)

        except KafkaError as exc:
            module.fail_json(msg=to_native(exc))

    def describe(self):
        ''' Describe kafka topics. '''

        if self.topic:
            # describe supports multiple topics
            topics = ','.join(self.topic)
            cmd = '%s --describe --zookeeper %s --topic %s' % (self.executable,
                                                               self.zookeeper,
                                                               topics)
        else:
            cmd = '%s --describe --zookeeper %s' % (self.executable,
                                                    self.zookeeper)

        try:
            return self.module.run_command(cmd)

        except KafkaError as exc:
            module.fail_json(msg=to_native(exc))

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
                    '--partitions %s --topic %s') % (self.executable,
                                                     self.zookeeper,
                                                     self.partitions,
                                                     topic)

        try:
            env = ''
            if self.jaas_auth_file:
                env = { 'KAFKA_OPTS': self.kafka_env_opts }

            if int(get_partitions) < int(self.partitions):
                return self.module.run_command(cmd, environ_update=env)
            else:
                err_msg="""
                The number of partitions for a topic can only be increased.
                """
                return self.module.fail_json(msg=to_native(err_msg))

        except KafkaError as exc:
            module.fail_json(msg=to_native(exc))

    def create(self):
        ''' Create new kafka topic. '''

        # create action supports only 1 topic
        if len(self.topic) > 1:
                msg = 'alter action supports only 1 topic'
                return self.module.fail_json(msg)
        else:
            topic = ''.join(self.topic)
            if self.config:
                config = ' --config '.join(
                    "%s=%r" % (key, value) for (key, value) in self.config.iteritems())

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
                        '--topic %s') % (self.executable,
                                         self.zookeeper,
                                         self.replication_factor,
                                         self.partitions,
                                         topic)

        try:
            env = ''
            if self.jaas_auth_file:
                env = { 'KAFKA_OPTS': self.kafka_env_opts }

            return self.module.run_command(cmd, environ_update=env)

        except KafkaError as exc:
            module.fail_json(msg=to_native(exc))

    def delete(self):
        ''' Delete a kafka topic. '''
        # create action supports only 1 topic
        if len(self.topic) > 1:
                msg = 'alter action supports only 1 topic'
                return self.module.fail_json(msg)
        else:
            topic = ''.join(self.topic)
            cmd = ('%s --delete --zookeeper %s '
                    '--topic %s --if-exists') % (self.executable,
                                                  self.zookeeper,
                                                  topic)

        try:
            env = ''
            if self.jaas_auth_file:
                env = { 'KAFKA_OPTS': self.kafka_env_opts }
            return self.module.run_command(cmd, environ_update=env)

        except KafkaError as exc:
            module.fail_json(msg=to_native(exc))

def main():
    argument_spec = dict(
        action = dict(default='list',
                        choices=['list', 'describe', 'alter',
                                 'create', 'delete'],
                        type='str'),
        topic = dict(type='list'),
        config = dict(type='dict'),
        zookeeper = dict(required=True, type='list'),
        replication_factor = dict(type='int'),
        partitions = dict(type='int'),
        kafka_path = dict(default='/opt/kafka',
                                type='path'),
        jaas_auth_file = dict(type='path'),
    )

    required_if = [
        ['action', 'alter',
         [ 'topic', 'partitions', ]
         ],
        ['action', 'create',
         [ 'topic', 'replication_factor', 'partitions', ]
         ],
        ['action', 'delete',
         [ 'topic', ]
         ],
    ]

    module = AnsibleModule(
        argument_spec = argument_spec,
        required_if = required_if,
        supports_check_mode = True,
    )

    kafka_bin = module.params['kafka_path'] + '/bin/kafka-topics.sh'
    jaas_auth_file = module.params['jaas_auth_file']

    is_kafka_bin = os.path.isfile(kafka_bin)
    
    changed = False

    if not is_kafka_bin:
        module.fail_json(msg='%s not found.' % (kafka_bin))

    if module.params['jaas_auth_file']:
        is_jaas_auth_file = os.path.isfile(jaas_auth_file)
        if not is_jaas_auth_file:
           module.fail_json(msg='%s not found.' % (jaas_auth_file))

    try:
        kt = KafkaTopics(module)

        action = module.params['action']
        if not module.check_mode:
            if module.params['action'] == 'list':
                (rc, out, err) = kt.get()
            elif module.params['action'] == 'describe':
                (rc, out, err) = kt.describe()
            elif module.params['action'] == 'alter':
                (rc, out, err) = kt.alter()
                if re.search('Adding partitions succeeded!', out):
                    changed = True
            elif module.params['action'] == 'create':
                (rc, out, err) = kt.create()
                if re.search('^Created topic', out):
                    changed = True
            elif module.params['action'] == 'delete':
                (rc, out, err) = kt.delete()
                if re.search('^Topic [a-zA-Z0-9_\-]+ is marked for deletion.', out):
                    changed = True

            result = {
                    'stdout': out,
                    'stdout_lines': out.splitlines(),
                    'stderr': err,
                    'rc': rc,
                    'changed': changed,
            }
            
    except KafkaError as exc:
        module.fail_json(msg=to_native(exc))

    module.exit_json(**result)

if __name__ == '__main__':
    main()
