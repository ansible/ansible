#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Steve Gargan <steve.gargan@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: consul_session
short_description: Manipulate consul sessions
description:
 - Allows the addition, modification and deletion of sessions in a consul
   cluster. These sessions can then be used in conjunction with key value pairs
   to implement distributed locks. In depth documentation for working with
   sessions can be found at http://www.consul.io/docs/internals/sessions.html
requirements:
  - python >= 2.6
  - python-consul
  - requests
version_added: "2.0"
author:
- Steve Gargan (@sgargan)
options:
    state:
        description:
          - Whether the session should be present i.e. created if it doesn't
            exist, or absent, removed if present. If created, the ID for the
            session is returned in the output. If absent, the name or ID is
            required to remove the session. Info for a single session, all the
            sessions for a node or all available sessions can be retrieved by
            specifying info, node or list for the state; for node or info, the
            node name or session id is required as parameter.
        choices: [ absent, info, list, node, present ]
        default: present
    name:
        description:
          - The name that should be associated with the session. This is opaque
            to Consul and not required.
    delay:
        description:
          - The optional lock delay that can be attached to the session when it
            is created. Locks for invalidated sessions ar blocked from being
            acquired until this delay has expired. Durations are in seconds.
        default: 15
    node:
        description:
          - The name of the node that with which the session will be associated.
            by default this is the name of the agent.
    datacenter:
        description:
          - The name of the datacenter in which the session exists or should be
            created.
    checks:
        description:
          - A list of checks that will be used to verify the session health. If
            all the checks fail, the session will be invalidated and any locks
            associated with the session will be release and can be acquired once
            the associated lock delay has expired.
    host:
        description:
          - The host of the consul agent defaults to localhost.
        default: localhost
    port:
        description:
          - The port on which the consul agent is running.
        default: 8500
    scheme:
        description:
          - The protocol scheme on which the consul agent is running.
        default: http
        version_added: "2.1"
    validate_certs:
        description:
          - Whether to verify the tls certificate of the consul agent.
        type: bool
        default: True
        version_added: "2.1"
    behavior:
        description:
          - The optional behavior that can be attached to the session when it
            is created. This controls the behavior when a session is invalidated.
        choices: [ delete, release ]
        default: release
        version_added: "2.2"
"""

EXAMPLES = '''
- name: register basic session with consul
  consul_session:
    name: session1

- name: register a session with an existing check
  consul_session:
    name: session_with_check
    checks:
      - existing_check_name

- name: register a session with lock_delay
  consul_session:
    name: session_with_delay
    delay: 20s

- name: retrieve info about session by id
  consul_session:
    id: session_id
    state: info

- name: retrieve active sessions
  consul_session:
    state: list
'''

try:
    import consul
    from requests.exceptions import ConnectionError
    python_consul_installed = True
except ImportError:
    python_consul_installed = False

from ansible.module_utils.basic import AnsibleModule


def execute(module):

    state = module.params.get('state')

    if state in ['info', 'list', 'node']:
        lookup_sessions(module)
    elif state == 'present':
        update_session(module)
    else:
        remove_session(module)


def lookup_sessions(module):

    datacenter = module.params.get('datacenter')

    state = module.params.get('state')
    consul_client = get_consul_api(module)
    try:
        if state == 'list':
            sessions_list = consul_client.session.list(dc=datacenter)
            # Ditch the index, this can be grabbed from the results
            if sessions_list and sessions_list[1]:
                sessions_list = sessions_list[1]
            module.exit_json(changed=True,
                             sessions=sessions_list)
        elif state == 'node':
            node = module.params.get('node')
            if not node:
                module.fail_json(
                    msg="node name is required to retrieve sessions for node")
            sessions = consul_client.session.node(node, dc=datacenter)
            module.exit_json(changed=True,
                             node=node,
                             sessions=sessions)
        elif state == 'info':
            session_id = module.params.get('id')
            if not session_id:
                module.fail_json(
                    msg="session_id is required to retrieve indvidual session info")

            session_by_id = consul_client.session.info(session_id, dc=datacenter)
            module.exit_json(changed=True,
                             session_id=session_id,
                             sessions=session_by_id)

    except Exception as e:
        module.fail_json(msg="Could not retrieve session info %s" % e)


def update_session(module):

    name = module.params.get('name')
    delay = module.params.get('delay')
    checks = module.params.get('checks')
    datacenter = module.params.get('datacenter')
    node = module.params.get('node')
    behavior = module.params.get('behavior')

    consul_client = get_consul_api(module)

    try:
        session = consul_client.session.create(
            name=name,
            behavior=behavior,
            node=node,
            lock_delay=delay,
            dc=datacenter,
            checks=checks
        )
        module.exit_json(changed=True,
                         session_id=session,
                         name=name,
                         behavior=behavior,
                         delay=delay,
                         checks=checks,
                         node=node)
    except Exception as e:
        module.fail_json(msg="Could not create/update session %s" % e)


def remove_session(module):
    session_id = module.params.get('id')
    if not session_id:
        module.fail_json(msg="""A session id must be supplied in order to
        remove a session.""")

    consul_client = get_consul_api(module)

    try:
        consul_client.session.destroy(session_id)

        module.exit_json(changed=True,
                         session_id=session_id)
    except Exception as e:
        module.fail_json(msg="Could not remove session with id '%s' %s" % (
                         session_id, e))


def get_consul_api(module):
    return consul.Consul(host=module.params.get('host'),
                         port=module.params.get('port'))


def test_dependencies(module):
    if not python_consul_installed:
        module.fail_json(msg="python-consul required for this module. "
                             "see https://python-consul.readthedocs.io/en/latest/#installation")


def main():
    argument_spec = dict(
        checks=dict(type='list'),
        delay=dict(type='int', default='15'),
        behavior=dict(type='str', default='release', choices=['release', 'delete']),
        host=dict(type='str', default='localhost'),
        port=dict(type='int', default=8500),
        scheme=dict(type='str', default='http'),
        validate_certs=dict(type='bool', default=True),
        id=dict(type='str'),
        name=dict(type='str'),
        node=dict(type='str'),
        state=dict(type='str', default='present', choices=['absent', 'info', 'list', 'node', 'present']),
        datacenter=dict(type='str'),
    )

    module = AnsibleModule(argument_spec, supports_check_mode=False)

    test_dependencies(module)

    try:
        execute(module)
    except ConnectionError as e:
        module.fail_json(msg='Could not connect to consul agent at %s:%s, error was %s' % (
            module.params.get('host'), module.params.get('port'), e))
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
