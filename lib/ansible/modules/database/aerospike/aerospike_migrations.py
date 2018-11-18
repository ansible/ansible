#!/usr/bin/python
"""short_description: Check or wait for migrations between nodes"""

# Copyright: (c) 2018, Albert Autin
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: aerospike_migrations
short_description: Check or wait for migrations between nodes
description:
    - This can be used to check for migrations in a cluster.
    - This makes it easy to do a rolling upgrade/update on Aerospike nodes.
    - If waiting for migrations is not desired, simply just poll until
    - port 3000 if available or asinfo -v status returns ok
version_added: 2.8
author: "Albert Autin github.com/Alb0t"
options:
    host:
        description:
            - Which host do we use as seed for info connection
        required: False
        type: str
        default: localhost
    port:
        description:
            - Which port to connect to Aerospike on (service port)
        required: False
        type: int
        default: 3000
    connect_timeout:
        description:
            - How long to try to connect to node before giving up (ms)
        required: False
        type: int
        default: 1000
    consecutive_good_checks:
        description:
            - How many times should the cluster report "no migrations"
            - consecutively before returning OK back to ansible?
        required: False
        type: int
        default: 3
    sleep_between_checks:
        description:
            - How long to sleep between each check (seconds).
        required: False
        type: int
        default: 60
    tries_limit:
        description:
            - How many times do we poll before giving up and failing?
        default: 300
        required: False
        type: int
    local_only:
        description:
            - Do you wish to only check for migrations on the local node
            - before returning, or do you want all nodes in the cluster
            - to finish before returning?
        required: False
        type: bool
'''
EXAMPLES = '''
# check for migrations on local node
- name: wait for migrations on local node before proceeding
  aerospike_migrations:
    host: "localhost"
    connect_timeout: 2000
    consecutive_good_checks: 5
    sleep_between_checks: 15
    tries_limit: 600
    local_only: False

# example playbook:
---
- name: upgrade aerospike
  hosts: all
  become: true
  serial: 1
  tasks:
    - name: Install dependencies
      apt:
        name:
            - python
            - python-pip
            - python-setuptools
        state: latest
    - name: setup aerospike
      pip:
          name: aerospike
    - name: wait for no migrations
      aerospike_migrations:
          local_only: false
          sleep_between_checks: 1
    - name: another thing
      shell: |
          echo foo
    - name: reboot
      reboot:
'''

RETURN = '''
# im not real sure what goes here
'''
from time import sleep
from ansible.module_utils.basic import AnsibleModule

try:
    import aerospike
except ImportError:
    AEROSPIKE_LIB_FOUND = False
else:
    AEROSPIKE_LIB_FOUND = True


def run_module():
    """run ansible module"""
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        host=dict(type='str', required=False, default='localhost'),
        port=dict(type='int', required=False, default=3000),
        connect_timeout=dict(type='int', required=False, default=1000),
        consecutive_good_checks=dict(type='int', required=False, default=3),
        sleep_between_checks=dict(type='int', required=False, default=60),
        tries_limit=dict(type='int', requires=False, default=300),
        local_only=dict(type='bool', required=True)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    if not AEROSPIKE_LIB_FOUND:
        module.fail_json(
            msg='Aerospike module not found.' +
            'Please run "pip install aerospike".')

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    migrations = Migrations(module)
    # migrations.has_migs accepts 1 argument,
    # a bool to specify checking local node only or entire cluster
    has_migs = migrations.has_migs(module.params['local_only'])
    if has_migs is False:
        result['message'] = "No migrations"
    else:
        result['message'] = "Migrations still found after reaching limit."
        module.fail_json(
            msg="Migrations still found after reaching tries limit.")

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    #    if module.params['new']:
    #        result['changed'] = True

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    #    if module.params['name'] == 'fail me':
    #        module.fail_json(msg='You requested this to fail', **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


class Migrations:
    """short_description: Check or wait for migrations between nodes"""
    # TODO: add support for auth, tls, and other special features
    def __init__(self, module):
        config = {
            'hosts': [
                (module.params['host'], module.params['port'])
            ],
            'policies': {
                'timeout': module.params['connect_timeout']  # milliseconds
            }
        }
        self.module = module
        self.client = aerospike.client(config)
        self.client.connect()
        self._update_nodes_list()
        self._update_statistics()
        self._update_namespace_list()
        self.consecutive_good_required = \
            module.params['consecutive_good_checks']
        self.sleep_between = module.params['sleep_between_checks']
        self.tries_limit = module.params['tries_limit']

    # delimiter is for seperate stats that come back, NOT for kv
    # seperation which is =
    def _info_cmd_helper(self, cmd, node, delimiter=';'):
        if node is None:
            node = self.nodes[0]

        data = self.client.info_node(cmd, node).split("\t")[1]
        # TODO: is there a better way to
        # clean the command off the output?
        data = data.rstrip("\n\r")
        data_arr = data.split(delimiter)

        # some commands don't return in kv format
        # , so we dont want a dict from those.
        if '=' in data:
            retval = dict(
                metric.split("=") for metric in data.split(delimiter))
        else:
            retval = data_arr
        return retval

    def _update_namespace_list(self, node=None):
        self.namespaces = self._info_cmd_helper('namespaces', node)

    def _update_statistics(self, node=None):
        self.statistics = self._info_cmd_helper('statistics', node)

    def _update_nodes_list(self):
        self.nodes = self.client.get_nodes()

    def _namespace_has_migs(self, namespace, node=None):
        namespace_stats = self._info_cmd_helper("namespace/" + namespace, node)
        try:
            namespace_tx = \
                int(namespace_stats["migrate_tx_partitions_remaining"])
            namespace_rx = \
                int(namespace_stats["migrate_rx_partitions_remaining"])
            test = int(namespace_tx) + 1
            test = int(namespace_rx) + 1
        except KeyError:
            self.module.fail_json(
                msg="Did not find partition remaining key in output"
            )
        except TypeError:
            self.module.fail_json(
                msg="namespace stat returned was not numerical"
            )

        if namespace_tx != 0 or namespace_rx != 0:
            return True
        if namespace_tx == 0 and namespace_rx == 0:
            return False

    def _node_has_migs(self, node=None):
        self._update_namespace_list(node)
        migs = 0
        for namespace in self.namespaces:
            if self._namespace_has_migs(namespace, node) is True:
                migs += 1
        if migs != 0:
            return True
        return False

    def _local_node_has_migs(self):
        return self._node_has_migs()

    def _cluster_has_migs(self):
        migs = 0
        self._update_nodes_list()
        for node in self.nodes:
            if self._node_has_migs(node) is True:
                migs += 1
        if migs != 0:
            return True
        return False

    def _has_migs(self, local):
        if local is True:
            return self._local_node_has_migs()
        return self._cluster_has_migs()

    def has_migs(self, local=True):
        """returns a boolean, False if no migrations otherwise True"""
        consecutive_good = 0
        try_num = 0
        while \
                try_num < self.tries_limit and \
                        consecutive_good < self.consecutive_good_required:
            if self._has_migs(local) is True:
                consecutive_good = 0
            elif self._has_migs(local) is False:
                consecutive_good += 1
                if consecutive_good is self.consecutive_good_required:
                    break
            try_num += 1
            sleep(self.sleep_between)
        if consecutive_good is self.consecutive_good_required:
            return False
        return True

def main():
    """main method for ansible module"""
    run_module()

if __name__ == '__main__':
    main()
