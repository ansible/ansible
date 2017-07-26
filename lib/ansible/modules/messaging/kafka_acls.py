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
module: kafka_acls
author: "Guillaume Delpierre (@gdelpierre)"
version_added: "2.4"
short_description: Add/Remove ACLs config.
description:
    - 'Add/Remove ACLs config for a topic, producer, consummer or cluster'
requirements:
    - 'kafka-acls.sh'
options:
    action:
        required: True
        type: str
        choices: ['add', 'list', 'remove']
        description:
            - Add, list or remove ACLs.
              For list, use topic, or group or cluster to specify a resource.
    allow_host:
        required: False
        type: list
        description:
            - Host from which principals listed in allow-principal will have access.
    allow_principal:
        required: False
        type: list
        description:
            - Principal is in principalType:name format.
              Note that principalType must be supported by the Authorizer being used.
    authorizer:
        required: False
        type: str
        description:
            - Fully qualified class name of the authorizer.
              Defaults to kafka.security.auth.SimpleAclAuthorizer.
    authorizer_properties:
        required: True
        type: str
        description:
            - Properties required to configure an instance of Authorizer.
              These are key=val pairs.
    cluster:
        required: False
        type: str
        description:
            - Add/Remove cluster ACLs.
    consumer:
        required: False
        default: False
        type: bool
        choices: [True, False]
        description:
            - Convenience option to add/remove ACLs for consumer role.
    deny_host:
        required: False
        type: list
        description:
            - Host from which principals listed in deny-principal will be denied access.
    deny_principal:
        required: False
        type: list
        description:
            - By default anyone not added through allow-principal is denied access.
              You only need to use this option as negation to already allowed set.
    group:
        required: False
        type: list
        description:
            - Consumer Group to which the ACLs should be added or removed.
    operation:
        required: False
        type: list
        description:
            - Operation that is being allowed or denied.
    producer:
        required: False
        default: False
        type: bool
        choices: [True, False]
        description:
            - Convenience option to add/remove ACLs for producer role.
    topic:
        required: False
        type: str
        description:
            - Topic to which ACLs should be added or removed.
    jaas_auth_file:
        required: False
        type: str
        description:
            - JAAS authentification file.
    kafka_path:
        required: False
        type: path
        default: '/opt/kafka'
        description:
            - Kafka path.
'''

EXAMPLES = '''
name: 'add ACLs'
kafka_acls:
  action: 'add'
  kafka_path: '/home/foobar/kafka/'
  authorizer_properties: 'zookeeper.connect=localhost:2181'
  jaas_auth_file: 'jaas-kafka.conf'
  topic: 'croziflette'
  allow_principal:
    - 'User:bar'
  operation:
    - read
    - write
  allow_host:
    - '127.0.0.1'

name: 'modify ACLs'
kafka_acls:
  action: 'add'
  jaas_auth_file: 'jaas-kafka.conf'
  authorizer_properties: 'zookeeper.connect=localhost:2181'
  topic: 'croziflette'
  deny_principal:
    - 'User:baz'
    - 'User:ANONYMOUS'
  operation:
    - describe
  deny_host:
    - '10.0.0.4'

name: 'list ACLs'
kafka_acls:
  action: 'list'
  jaas_auth_file: 'jaas-kafka.conf'
  authorizer_properties: 'zookeeper.connect=localhost:2181'
  topic: 'croziflette'

name: 'list all ACLs'
kafka_acls:
  action: 'list'
  jaas_auth_file: 'jaas-kafka.conf'
  authorizer_properties: 'zookeeper.connect=localhost:2181'

name: 'remove ACLs'
kafka_acls:
  action: 'remove'
  jaas_auth_file: 'jaas-kafka.conf'
  authorizer_properties: 'zookeeper.connect=localhost:2181'
  topic: 'croziflette'
  operation:
    - 'describe'
'''

RETURN = '''
'''

import os.path

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils._text import to_native

class KafkaError(Exception):
    pass
 
class KafkaAcls(object):

    def __init__(self, module):
        self.action = module.params['action']
        self.allow_host = module.params['allow_host']
        self.allow_principal = module.params['allow_principal']
        self.authorizer = module.params['authorizer']
        self.authorizer_properties = module.params['authorizer_properties']
        self.consumer = module.params['consumer']
        self.cluster = module.params['cluster']
        self.deny_host = module.params['deny_host']
        self.deny_principal = module.params['deny_principal']
        self.group = module.params['group']
        self.operation = module.params['operation']
        self.producer = module.params['producer']
        self.topic = module.params['topic']

        self.authentification = module.params['kafka_path'] + \
                                '/config/' + module.params['jaas_auth_file']
        self.executable = module.params['kafka_path'] + '/bin/kafka-acls.sh'
        self.kafka_env_opts = '-Djava.security.auth.login.config=' + \
                                self.authentification

        self.module = module

    def get(self):
        ''' List kafka ACLs. '''
        
        mod_args = {
                '--authorizer': self.authorizer,
                '--authorizer-properties': self.authorizer_properties,
                '--topic': self.topic,
        }

        mod_args_join = ''.join(" %s %r" % (k, v) for k,v in mod_args.iteritems() if v)

        cmd = '%s --list %s' % (self.executable, mod_args_join)

        try:
            env = { 'KAFKA_OPTS': self.kafka_env_opts }
            return self.module.run_command(cmd, environ_update=env)

        except:
            e = get_exception()
            raise KafkaError(e)

    def addrem(self):
        ''' Add or Remove ACLs. '''

        mod_args = {
                '--allow-host': self.allow_host,
                '--allow-principal': self.allow_principal,
                '--deny-host': self.deny_host,
                '--deny-principal': self.deny_principal,
                '--group': self.group,
                '--operation': self.operation,
                '--topic': self.topic,
        }

        auth_args = {
                '--authorizer': self.authorizer,
                '--authorizer-properties': self.authorizer_properties,
        }

        mod_args_join = ''
        for k,v in mod_args.iteritems():
            if v:
                if isinstance(v, list):
                    for item in v:
                        mod_args_join += ''.join(" %s %r" % (k, item))
                else:
                    mod_args_join += ''.join(" %s %r" % (k, v))

        mod_auth_join = ''.join(" %s %r" % (k, v) for k,v in auth_args.iteritems() if v)

        if self.producer:
            cmd = '%s %s --%s --producer %s' % (self.executable, mod_auth_join,
                                                self.action, mod_args_join)
        elif self.consumer:
            cmd = '%s %s --%s --consumer %s' % (self.executable, mod_auth_join,
                                                self.action, mod_args_join)
        elif self.action == 'remove':
            cmd = '%s %s --force --%s %s' % (self.executable, mod_auth_join,
                                                self.action, mod_args_join)
        else:
            cmd = '%s %s --%s %s' % (self.executable, mod_auth_join,
                                        self.action, mod_args_join)

        try:
            env = { 'KAFKA_OPTS': self.kafka_env_opts }
            return self.module.run_command(cmd, environ_update=env)

        except:
            e = get_exception()
            raise KafkaError(e)


def main():
    argument_spec = dict(
            action=dict(required=True, choices=['list', 'add', 'remove'],
                        type='str'),
            allow_host=dict(required=False, type='list'),
            allow_principal=dict(required=False, type='list'),
            authorizer=dict(required=False, type='str'),
            authorizer_properties=dict(required=True, type='str'),
            cluster=dict(required=False, type='str'),
            consumer=dict(required=False, default=False,
                            choices=[ True, False ], type='bool'),
            deny_host=dict(required=False, type='list'),
            deny_principal=dict(required=False, type='list'),
            group=dict(required=False, type='list'),
            operation=dict(required=False, type='list'),
            producer=dict(required=False, default=False,
                            choices=[ True, False ], type='bool'),
            topic=dict(required=False, type='str'),

            jaas_auth_file = dict(required=True, type='str'),
            kafka_path = dict(required=False, default='/opt/kafka',
                                type='path'),
    )

    required_one_of = [
            ['topic', 'cluster', 'group']
    ]

    mutually_exclusive = [
            ['cluster', 'topic'],
    ]

    module = AnsibleModule(
        argument_spec = argument_spec,
        required_one_of = required_one_of,
        mutually_exclusive = mutually_exclusive,
        supports_check_mode = True,
    )

    kafka_bin = os.path.isfile(module.params['kafka_path'] + \
                    '/bin/kafka-acls.sh')
    jaas_auth_file = os.path.isfile(module.params['kafka_path'] + \
                        '/config/' + module.params['jaas_auth_file'])

    if not kafka_bin:
        module.fail_json(msg='%s not found.' % (kafka_bin))

    if not jaas_auth_file:
        module.fail_json(msg='%s not found.' % (jaas_auth_file))

    try:
        ka = KafkaAcls(module)

        action = module.params['action']
        if not module.check_mode:
            if action == 'list':
                (rc, out, err) = ka.get()
            else:
                (rc, out, err) = ka.addrem()
                
            result = {
                    'stdout': out,
                    'stdout_lines': out.splitlines(),
                    'stderr': err,
                    'stderr_lines': err.splitlines(),
                    'rc': rc,
            }

    except KafkaError as e:
        module.fail_json(msg=to_native(e))

    module.exit_json(**result)

if __name__ == '__main__':
    main()
