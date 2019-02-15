#!/usr/bin/python

# Copyright: (c) 2018, Christian Sandrini <mail@chrissandrini.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: serviceguard_pkg

short_description: This package controls serviceguard package state

version_added: "2.7"

description:
    - "This package controls the package state of a HP ServiceGuard retval"

options:
    name:
        description:
            - Name of the package
        required: true
    state:
        description:
            - State of the package
        required: true
        choices: [ started, stopped, restarted ]
        default: started
    node:
        description:
            - Name of the retval node
        required: false
    autorun:
        description:
            - Specifies whether a package should failover automatically
        required: false
        choices: [ enabled, disabled ]
        default: true
    path:
        description:
            - Path to the cm* binaries
        required: false
        default: /usr/local/cmcluster/bin

author:
    - Christian Sandrini (@sandrich)
    - Sergio Perez Fernandez (@sergioperez)
'''

EXAMPLES = '''
# Start package on its default node and make sure AUTO_RUN is set
- name: Start testpkg1 on default node
  serviceguard_pkg:
    name: testpkg1
    state: started
    autorun: enabled

# Start package on its default node
- name: Start testpkg1 on node1
  serviceguard_pkg:
    name: testpkg1
    state: started
    node: node1

# Stop package
- name: Stop testpkg1
  serviceguard_pkg:
    name: testpkg1
    state: stopped

# Stop all packages on node
- name: Stop all packages on node
  serviceguard_pkg:
    name: '*'
    state: stopped
'''

RETURN = '''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.serviceguard import parse_cluster_state
from enum import Enum


def stop_package(module, pkg_name):
    state = parse_cluster_state(module)

    stopped_package = None

    if pkg_name not in state['pkgs']:
        module.fail_json(msg="Package %s does not exist" % pkg_name)
    elif not (state['pkgs'][pkg_name]['state'] == 'halted'):
        # Halt package
        (rc, out, dummy) = module.run_command([module.params['path'] + '/cmhaltpkg', pkg_name])
        stopped_package = pkg_name

        if rc != 0:
            module.fail_json(msg="Failure %d stopping package %s with error:\n%s" % (rc, pkg_name, out))

    return stopped_package


def stop_all_packages(module, node):
    state = parse_cluster_state(module)

    stopped_packages = []

    if state['pkgs']:
        if node is None:
            stopped_packages = filter(lambda x: state['pkgs'][x]['state'] == 'running', state['pkgs'].keys())
        else:
            stopped_packages = filter(lambda x: state['pkgs'][x]['owner'] == node, state['pkgs'].keys())

        for pkg_name in stopped_packages:
            stop_package(module, pkg_name)

    return stopped_packages


class AutorunAction(Enum):
    NO_ACTION = -1
    ENABLED = 'enabled'
    DISABLED = 'disabled'


def set_autorun(module, desired_autorun_state, pkg_name):
    state = parse_cluster_state(module)
    current_autorun_state = state['pkgs'][pkg_name]['autorun']

    if desired_autorun_state == 'enabled':
        opt = '-e'
    else:
        opt = '-d'

    (rc, out, dummy) = module.run_command([module.params['path'] + '/cmmodpkg', opt, pkg_name])

    if rc != 0:
        module.fail_json(msg="Failure %d to modify package %s autorun state with error: %s" % (rc, pkg_name, out))

    performed_action = AutorunAction.NO_ACTION

    if current_autorun_state == desired_autorun_state:
        performed_action = desired_autorun_state

    return performed_action


def is_pkg_eligible_on_node(module, pkg, node):
        # Test if node is eligble
    (rc, out, dummy) = module.run_command([module.params['path'] + '/cmviewcl', '-f', 'line', '-p', pkg])

    return rc == 0 and out.find("node:%s" % node) > -1


# Tries to run the package and returns the new ServiceGuard state
def cmrunpkg(module, options):
    cmd = [module.params['path'] + '/cmrunpkg']

    # Start package
    (rc, out, dummy) = module.run_command(cmd + options)

    if rc == 1:
        module.fail_json(msg="Failure %d running cmviewcl with error: %s" % (rc, out))


def start_package(module):

    pkg_name = module.params['name']
    target_node = module.params['node']

    state = parse_cluster_state(module)
    current_pkg_state = state['pkgs'][pkg_name]['state']
    pkg_owner_node = state['pkgs'][pkg_name]['owner']

    if current_pkg_state == 'running':
        # Do not move it unless a node name
        if target_node is not None and target_node != pkg_owner_node:
            # Stop and start package on new node
            stop_package(module, pkg_name)
            start_package(module)

    elif current_pkg_state == 'halted':
        if target_node is None:
            # No node => start on default
            cmrunpkg(module, [pkg_name])

        else:
            # node => start it on it
            if not is_pkg_eligible_on_node(module, pkg_name, target_node):
                module.fail_json(msg="Package %s is not configured to run on %s" % (pkg_name, target_node))

            cmrunpkg(module, ['-n', target_node, pkg_name])

    return pkg_name


class ActionType(Enum):
    NO_ACTION = -1
    START = 0
    STOP = 1


class ActionTarget(Enum):
    NO_TARGET = -1
    SINGLE = 0
    MULTIPLE = 1


def main():
    # Initialise
    module_args = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', required=False, choices=['started', 'stopped', 'restarted'], default='started'),
        node=dict(type='str', required=False),
        autorun=dict(type='str', required=False, choices=['enabled', 'disabled'], default=True),
        path=dict(type='str', required=False, default='/usr/local/cmcluster/bin')
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    initial_state = parse_cluster_state(module)
    affected_packages = []
    desired_state = module.params['state']
    package_name = module.params['name']
    node_name = module.params['node']

    if desired_state == 'stopped':
        action_type = ActionType.STOP

        if package_name == '*':
            affected_packages = stop_all_packages(module, node_name)

        else:
            affected_packages.append(stop_package(module, package_name))

    elif desired_state == 'started':
        action_type = ActionType.START

        start_package(module)

    if module.params['autorun'] is not None:
        set_autorun(module, module.params['autorun'], module.params['name'])

    final_state = parse_cluster_state(module)
    final_state['changed'] = not(initial_state == final_state)

    # Append the started/stopped package list
    if action_type == ActionType.STOP:
        final_state['stopped_packages'] = affected_packages
    elif action_type == ActionType.START:
        final_state['started_packages'] = affected_packages

    module.exit_json(**final_state)


if __name__ == '__main__':
    main()
