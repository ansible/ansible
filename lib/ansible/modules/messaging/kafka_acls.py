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
module: kafka_acls
author: "Guillaume Delpierre (@gdelpierre)"
version_added: "2.5"

short_description: Add/Remove ACLs config.
description:
    - 'Add/Remove ACLs config for a topic, producer, consummer or cluster'
requirements:
    - 'kafka >= 2.11-0.10'
options:
    action:
        required: True
        choices: ['add', 'list', 'remove']
        description:
            - Add, list or remove ACLs.
              For list, use topic, or group or cluster to specify a resource.
    allow_host:
        description:
            - Host from which principals listed in allow-principal will have access.
    allow_principal:
        description:
            - Principal is in principalType:name format.
              Note that principalType must be supported by the Authorizer being used.
    authorizer:
        description:
            - Fully qualified class name of the authorizer.
              Defaults to kafka.security.auth.SimpleAclAuthorizer.
    authorizer_properties:
        required: True
        description:
            - Properties required to configure an instance of Authorizer.
              These are key=val pairs.
    cluster:
        description:
            - Add/Remove cluster ACLs.
    consumer:
        description:
            - Convenience option to add/remove ACLs for consumer role.
    deny_host:
        description:
            - Host from which principals listed in deny-principal will be denied access.
    deny_principal:
        description:
            - By default anyone not added through allow-principal is denied access.
              You only need to use this option as negation to already allowed set.
    group:
        description:
            - Consumer Group to which the ACLs should be added or removed.
    operation:
        description:
            - Operation that is being allowed or denied.
    producer:
        description:
            - Convenience option to add/remove ACLs for producer role.
    topic:
        description:
            - Topic to which ACLs should be added or removed.
    executable:
        description:
            - Kafka executable path if not in your current PATH or if it name differs.
'''

EXAMPLES = '''
name: 'add ACLs'
# If you have JAAS authentification,
# use environment variable
environment:
  KAFKA_OPTS: '-Djava.security.auth.login.config=/etc/kafka/jaas.conf'
kafka_acls:
  action: 'add'
  authorizer_properties: 'zookeeper.connect=localhost:2181'
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
  authorizer_properties: 'zookeeper.connect=localhost:2181'
  topic: 'croziflette'

name: 'list all ACLs'
kafka_acls:
  action: 'list'
  authorizer_properties: 'zookeeper.connect=localhost:2181'

name: 'remove ACLs'
kafka_acls:
  action: 'remove'
  authorizer_properties: 'zookeeper.connect=localhost:2181'
  topic: 'croziflette'
  operation:
    - 'describe'
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
  sample: "Adding ACLs for resource `Topic:flunk`: \\\\n \\\\tUser:albert has Allow permission for operations: Write from hosts: 127.0.0.1\\\\n"

msg:
  description: Output from stderr
  returned: failed
  type: string
  sample: ""
'''

import re
import os

from ansible.module_utils.basic import AnsibleModule, is_executable
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

        self.executable = module.params['executable'] or module.get_bin_path('kafka-acls', True)
        self.module = module

    def get(self):
        ''' List kafka ACLs. '''

        mod_args = {
            '--authorizer': self.authorizer,
            '--authorizer-properties': self.authorizer_properties,
            '--topic': self.topic,
        }

        mod_args_join = ''.join(
            " %s %r" % (key, value) for key, value
            in mod_args.items() if value)

        cmd = '%s --list %s' % (self.executable, mod_args_join)

        return self.module.run_command(cmd)

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
        for key, value in mod_args.items():
            if value:
                if isinstance(value, list):
                    for item in value:
                        mod_args_join += ''.join(" %s %r" % (key, item))
                else:
                    mod_args_join += ''.join(" %s %r" % (key, value))

        mod_auth_join = ''.join(
            " %s %r" % (key, value) for key, value
            in auth_args.items() if value)

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

        return self.module.run_command(cmd)


def main():
    argument_spec = dict(
        action=dict(required=True,
                    choices=['list', 'add', 'remove'],
                    type='str'),
        allow_host=dict(type='list'),
        allow_principal=dict(type='list'),
        authorizer=dict(type='str'),
        authorizer_properties=dict(required=True, type='str'),
        cluster=dict(type='str'),
        consumer=dict(default=False, type='bool'),
        deny_host=dict(type='list'),
        deny_principal=dict(type='list'),
        group=dict(type='list'),
        operation=dict(type='list'),
        producer=dict(default=False, type='bool'),
        topic=dict(type='str'),
        executable=dict(type='path'),
    )

    required_one_of = [
        ['topic', 'cluster', 'group']
    ]

    mutually_exclusive = [
        ['cluster', 'topic'],
    ]

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=required_one_of,
        mutually_exclusive=mutually_exclusive,
    )

    changed = False
    failed = False
    result = {}

    if not module.get_bin_path('kafka-acls') and module.params['executable'] is None:
        module.fail_json(msg='Executable not provided.')
    if module.params['executable'] is not None and \
            (not os.path.isfile(module.params['executable']) or
             not is_executable(module.params['executable'])):
        module.fail_json(msg='%s not found or not executable.' % (module.params['executable']))

    try:
        ka = KafkaAcls(module)

        action = module.params['action']
        if not module.check_mode:
            if action == 'list':
                (rc, out, err) = ka.get()
            else:
                # yeah, it's ugly,
                # yeah, it's slow,
                # but we need to know if something has changed
                (_, out_list_before, _) = ka.get()
                (rc, out, err) = ka.addrem()
                (_, out_list_after, _) = ka.get()
                if out_list_before != out_list_after:
                    changed = True

        if re.search('^Error while executing ACL command:', out):
            module.fail_json(msg=out)

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
