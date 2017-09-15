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
module: kafka_topics
author: "Guillaume Delpierre (@gdelpierre)"
version_added: "2.5"

short_description: Deal with kafka topics.
description:
    - "Alter/Create/Delete kafka topics"
requirements:
    - "kafka-topics"
options:
    action:
        default: list
        choices: ['list', 'describe', 'alter', 'create', 'delete']
        description:
            - Specifies the action you want to perform.
    topic:
        description:
            - The topic to be create, alter or describe (single).
              The topics to be describe or list (multiple).
    config:
        description:
            - A topic configuration override for the topic being created.
    zookeeper:
        required: True
        description:
            - The connection string for the ZooKeeper connection.
              Multiple connection strings are allowed.
    replication_factor:
        description:
            -  The replication factor for each partition in the topic being created.
    partitions:
        description:
            - The number of partitions for the topic being created or altered.
    executable:
        description:
            - Kafka executable path if not in your current PATH or if it name differs.
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
  zookeeper:
    - zookeeper1.foo.bar:2181
    - zookeeper2.foo.bar:2181

# If you have JAAS authentification,
# use environment variable
name: 'Create topic foobar'
environment:
  KAFKA_OPTS: '-Djava.security.auth.login.config=/etc/kafka/jaas.conf'
kafka_topics:
  action: 'create'
  topic: 'foobar'
  config:
    cleanup.policy: 'delete'
    compression.type: 'gzip'
  partitions: 2
  replication_factor: 1
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
  zookeeper:
    - zookeeper1.foo.bar:2181
    - zookeeper2.foo.bar:2181

name: 'delete topic foobar'
kafka_topics:
  action: 'delete'
  topic: 'foobar'
  zookeeper:
    - zookeeper1.foo.bar:2181
    - zookeeper2.foo.bar:2181
'''

RETURN = '''
stdout:
  description: Output from stdout of kafka-topics command after execution of given command.
  returned: success or changed
  type: string
  sample: "Created topic raclette"

stderr:
  description: kafka-topics command execution stderr.
  returned: failed
  type: string
  sample: "[2017-07-11 14:46:04,092] ERROR org.apache.kafka.common.errors.InvalidTopicException: topic name [foobar] is illegal"

failed:
  description: kafka-topics command execution return bool.
  returned: always
  type: bool
  sample: False
'''

import re
import os

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


class KafkaError(Exception):
    pass


class KafkaTopics(object):

    def __init__(self, module):

        if module.params['config']:
            self.config = ''.join(' --config %s=%r' % (key, value) for (key, value)
                                  in module.params['config'].items())
        else:
            self.config = ''

        self.partitions = module.params['partitions']
        self.replication_factor = module.params['replication_factor']
        self.topic = module.params['topic']
        self.zookeeper = ','.join(module.params['zookeeper'])
        self.action = module.params['action']

        self.executable = module.params['executable'] or module.get_bin_path('kafka-topics', True)

        self.module = module

    def get(self):
        ''' List or Describe kafka topics. '''

        if self.topic:
            cmd = '%s --%s --zookeeper %s --topic %s' % (self.executable,
                                                         self.action,
                                                         self.zookeeper,
                                                         ','.join(self.topic))
        else:
            cmd = "%s --%s --zookeeper %s" % (self.executable,
                                              self.action,
                                              self.zookeeper)

        return self.module.run_command(cmd)

    def alter(self):
        ''' alter kafka topics. '''

        self.action = 'describe'
        cmd_get_partitions = self.get()
        # For a specific topic, we want the PartitionCount value.
        get_partitions = (cmd_get_partitions[1]
                          .splitlines()[0]
                          .split('\t')[1]
                          .split(':')[1]
                          )
        # alter supports only 1 topic
        if len(self.topic) > 1:
            msg = 'alter action supports only 1 topic, %s provided' % (len(self.topic))
            return self.module.fail_json(msg)
        else:
            cmd = ('%s --alter --if-exists --zookeeper %s '
                   '--partitions %s --topic %s') % (self.executable,
                                                    self.zookeeper,
                                                    self.partitions,
                                                    self.topic[0])

        if int(get_partitions) < int(self.partitions):
            return self.module.run_command(cmd)
        else:
            err_msg = """
            The number of partitions for a topic can only be increased.
            """
            return self.module.fail_json(msg=to_native(err_msg))

    def create(self):
        ''' Create new kafka topic. '''

        # create action supports only 1 topic
        if len(self.topic) > 1:
                msg = 'create action supports only 1 topic, %s provided' % (len(self.topic))
                return self.module.fail_json(msg)
        else:
            if self.config:
                cmd = ('%s --create --if-not-exists --zookeeper %s '
                       '--replication-factor %s --partitions %s '
                       '--topic %s %s') % (self.executable,
                                           self.zookeeper,
                                           self.replication_factor,
                                           self.partitions,
                                           ''.join(self.topic),
                                           self.config)

            else:
                cmd = ('%s --create --if-not-exists --zookeeper %s '
                       '--replication-factor %s --partitions %s '
                       '--topic %s') % (self.executable,
                                        self.zookeeper,
                                        self.replication_factor,
                                        self.partitions,
                                        ''.join(self.topic))

        return self.module.run_command(cmd)

    def delete(self):
        ''' Delete a kafka topic. '''

        # delete action supports only 1 topic
        if len(self.topic) > 1:
            msg = 'delete action supports only 1 topic, %s provided' % (len(self.topic))
            return self.module.fail_json(msg)
        else:
            cmd = ('%s --delete --zookeeper %s '
                   '--topic %s --if-exists') % (self.executable,
                                                self.zookeeper,
                                                self.topic[0])

        return self.module.run_command(cmd)


def main():
    argument_spec = dict(
        action=dict(default='list',
                    choices=['list', 'describe', 'alter',
                             'create', 'delete'],
                    type='str'),
        topic=dict(type='list'),
        config=dict(type='dict'),
        zookeeper=dict(required=True, type='list'),
        replication_factor=dict(type='int'),
        partitions=dict(type='int'),
        executable=dict(default='/usr/bin/kafka-topics',
                        type='path'),
    )

    required_if = [
        ['action', 'alter', ['topic', 'partitions']],
        ['action', 'create',
         ['topic', 'replication_factor', 'partitions']
         ],
        ['action', 'delete', ['topic']],
    ]

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=required_if,
        supports_check_mode=False,
    )

    changed = False
    failed = False

    if module.params['executable']:
        if not os.path.isfile(module.params['executable']):
            module.fail_json(msg='%s not found.' % (module.params['executable']))

    try:
        kt = KafkaTopics(module)

        action = module.params['action']
        if module.params['action'] == 'list' or module.params['action'] == 'describe':
            (rc, out, err) = kt.get()
        elif module.params['action'] == 'alter':
            (rc, out, err) = kt.alter()
            if re.search('Adding partitions succeeded!', out):
                changed = True
        elif module.params['action'] == 'create':
            (rc, out, err) = kt.create()
            if re.search('^Created topic', out):
                changed = True
            if not out:
                out = 'Nothing has changed.'
        elif module.params['action'] == 'delete':
            (rc, out, err) = kt.delete()
            if re.search('^Topic [a-zA-Z0-9_\-]+ is marked for deletion.', out):
                changed = True

        if rc != 0:
            failed = True

        result = {
            'stdout': out,
            'stderr': err,
            'failed': failed,
            'changed': changed,
        }

    except KafkaError as exc:
        module.fail_json(msg=to_native(exc))

    module.exit_json(**result)

if __name__ == '__main__':
    main()
