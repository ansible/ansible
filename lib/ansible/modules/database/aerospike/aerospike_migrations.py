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
      This makes it easy to do a rolling upgrade/update on Aerospike nodes.
    - If waiting for migrations is not desired, simply just poll until
      port 3000 if available or asinfo -v status returns ok
version_added: 2.8
author: "Albert Autin (@Alb0t)"
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
            - How long to try to connect before giving up (milliseconds)
        required: False
        type: int
        default: 1000
    consecutive_good_checks:
        description:
            - How many times should the cluster report "no migrations"
              consecutively before returning OK back to ansible?
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
              before returning, or do you want all nodes in the cluster
              to finish before returning?
        required: True
        type: bool
    min_cluster_size:
        description:
            - Check will return bad until cluster size is met
              or until tries is exhausted
        required: False
        type: int
        default: 1
    fail_on_cluster_change:
        description:
            - Fail if the cluster key changes
              if something else is changing the cluster, we may want to fail
        required: False
        type: bool
        default: True
    migrate_tx_key:
        description:
            - The metric key used to determine if we have tx migrations
              remaining. Changeable due to backwards compatibility.
        required: False
        type: str
        default: migrate_tx_partitions_remaining
    migrate_rx_key:
        description:
            - The metric key used to determine if we have rx migrations
              remaining. Changeable due to backwards compatibility.
        required: False
        type: str
        default: migrate_rx_partitions_remaining
    target_cluster_size:
        description:
            - When all aerospike builds in the cluster are greater than
              version 4.3, then the C(cluster-stable) info command will be used.
              Inside this command, you can optionally specify what the target
              cluster size is - but it is not necessary. You can still rely on
              min_cluster_size if you don't want to use this option.
            - If this option is specified on a cluster that has at least 1
              host <4.3 then it will be ignored until the min version reaches
              4.3.
        required: False
        type: int
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
# check for migrations every (sleep_between_checks)
# If at least (consecutive_good_checks) checks come back OK in a row, then return OK.
# Will exit if any exception, which can be caused by bad nodes,
# nodes not returning data, or other reasons.
# Maximum runtime before giving up in this case will be:
# Tries Limit * Sleep Between Checks * delay * retries
    - name: wait for aerospike migrations
      aerospike_migrations:
          local_only: True
          sleep_between_checks: 1
          tries_limit: 5
          consecutive_good_checks: 3
          fail_on_cluster_change: true
          min_cluster_size: 3
          target_cluster_size: 4
      register: migrations_check
      until: migrations_check is succeeded
      changed_when: false
      delay: 60
      retries: 120
    - name: another thing
      shell: |
          echo foo
    - name: reboot
      reboot:
'''

RETURN = '''
# Returns only a success/failure result. Changed is always false.
'''

import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

LIB_FOUND_ERR = None
try:
    import aerospike
    from time import sleep
    import re
except ImportError as ie:
    LIB_FOUND = False
    LIB_FOUND_ERR = traceback.format_exc()
else:
    LIB_FOUND = True


def run_module():
    """run ansible module"""
    module_args = dict(
        host=dict(type='str', required=False, default='localhost'),
        port=dict(type='int', required=False, default=3000),
        connect_timeout=dict(type='int', required=False, default=1000),
        consecutive_good_checks=dict(type='int', required=False, default=3),
        sleep_between_checks=dict(type='int', required=False, default=60),
        tries_limit=dict(type='int', requires=False, default=300),
        local_only=dict(type='bool', required=True),
        min_cluster_size=dict(type='int', required=False, default=1),
        target_cluster_size=dict(type='int', required=False, default=None),
        fail_on_cluster_change=dict(type='bool', required=False, default=True),
        migrate_tx_key=dict(type='str', required=False,
                            default="migrate_tx_partitions_remaining"),
        migrate_rx_key=dict(type='str', required=False,
                            default="migrate_rx_partitions_remaining")
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    if not LIB_FOUND:
        module.fail_json(msg=missing_required_lib('aerospike'),
                         exception=LIB_FOUND_ERR)

    try:
        if module.check_mode:
            has_migrations, skip_reason = False, None
        else:
            migrations = Migrations(module)
            has_migrations, skip_reason = migrations.has_migs(
                module.params['local_only']
            )

        if has_migrations:
            module.fail_json(msg="Failed.", skip_reason=skip_reason)
    except Exception as e:
        module.fail_json(msg="Error: {0}".format(e))

    module.exit_json(**result)


class Migrations:
    """ Check or wait for migrations between nodes """

    def __init__(self, module):
        self.module = module
        self._client = self._create_client().connect()
        self._nodes = {}
        self._update_nodes_list()
        self._cluster_statistics = {}
        self._update_cluster_statistics()
        self._namespaces = set()
        self._update_cluster_namespace_list()
        self._build_list = set()
        self._update_build_list()
        self._start_cluster_key = \
            self._cluster_statistics[self._nodes[0]]['cluster_key']

    def _create_client(self):
        """ TODO: add support for auth, tls, and other special features
         I won't use those features, so I'll wait until somebody complains
         or does it for me (Cross fingers)
         create the client object"""
        config = {
            'hosts': [
                (self.module.params['host'], self.module.params['port'])
            ],
            'policies': {
                'timeout': self.module.params['connect_timeout']
            }
        }
        return aerospike.client(config)

    def _info_cmd_helper(self, cmd, node=None, delimiter=';'):
        """delimiter is for seperate stats that come back, NOT for kv
        separation which is ="""
        if node is None:  # If no node passed, use the first one (local)
            node = self._nodes[0]
        data = self._client.info_node(cmd, node)
        data = data.split("\t")
        if len(data) != 1 and len(data) != 2:
            self.module.fail_json(
                msg="Unexpected number of values returned in info command: " +
                str(len(data))
            )
        # data will be in format 'command\touput'
        data = data[-1]
        data = data.rstrip("\n\r")
        data_arr = data.split(delimiter)

        # some commands don't return in kv format
        # so we dont want a dict from those.
        if '=' in data:
            retval = dict(
                metric.split("=", 1) for metric in data_arr
            )
        else:
            # if only 1 element found, and not kv, return just the value.
            if len(data_arr) == 1:
                retval = data_arr[0]
            else:
                retval = data_arr
        return retval

    def _update_build_list(self):
        """creates self._build_list which is a unique list
        of build versions."""
        self._build_list = set()
        for node in self._nodes:
            build = self._info_cmd_helper('build', node)
            self._build_list.add(build)

    # just checks to see if the version is 4.3 or greater
    def _can_use_cluster_stable(self):
        # if version <4.3 we can't use cluster-stable info cmd
        # regex hack to check for versions beginning with 0-3 or
        # beginning with 4.0,4.1,4.2
        if re.search(R'^([0-3]\.|4\.[0-2])', min(self._build_list)):
            return False
        return True

    def _update_cluster_namespace_list(self):
        """ make a unique list of namespaces
        TODO: does this work on a rolling namespace add/deletion?
        thankfully if it doesnt, we dont need this on builds >=4.3"""
        self._namespaces = set()
        for node in self._nodes:
            namespaces = self._info_cmd_helper('namespaces', node)
            for namespace in namespaces:
                self._namespaces.add(namespace)

    def _update_cluster_statistics(self):
        """create a dict of nodes with their related stats """
        self._cluster_statistics = {}
        for node in self._nodes:
            self._cluster_statistics[node] = \
                self._info_cmd_helper('statistics', node)

    def _update_nodes_list(self):
        """get a fresh list of all the nodes"""
        self._nodes = self._client.get_nodes()
        if not self._nodes:
            self.module.fail_json("Failed to retrieve at least 1 node.")

    def _namespace_has_migs(self, namespace, node=None):
        """returns a True or False.
        Does the namespace have migrations for the node passed?
        If no node passed, uses the local node or the first one in the list"""
        namespace_stats = self._info_cmd_helper("namespace/" + namespace, node)
        try:
            namespace_tx = \
                int(namespace_stats[self.module.params['migrate_tx_key']])
            namespace_rx = \
                int(namespace_stats[self.module.params['migrate_tx_key']])
        except KeyError:
            self.module.fail_json(
                msg="Did not find partition remaining key:" +
                self.module.params['migrate_tx_key'] +
                " or key:" +
                self.module.params['migrate_rx_key'] +
                " in 'namespace/" +
                namespace +
                "' output."
            )
        except TypeError:
            self.module.fail_json(
                msg="namespace stat returned was not numerical"
            )
        return namespace_tx != 0 or namespace_rx != 0

    def _node_has_migs(self, node=None):
        """just calls namespace_has_migs and
        if any namespace has migs returns true"""
        migs = 0
        self._update_cluster_namespace_list()
        for namespace in self._namespaces:
            if self._namespace_has_migs(namespace, node):
                migs += 1
        return migs != 0

    def _cluster_key_consistent(self):
        """create a dictionary to store what each node
        returns the cluster key as. we should end up with only 1 dict key,
        with the key being the cluster key."""
        cluster_keys = {}
        for node in self._nodes:
            cluster_key = self._cluster_statistics[node][
                'cluster_key']
            if cluster_key not in cluster_keys:
                cluster_keys[cluster_key] = 1
            else:
                cluster_keys[cluster_key] += 1
        if len(cluster_keys.keys()) == 1 and \
                self._start_cluster_key in cluster_keys:
            return True
        return False

    def _cluster_migrates_allowed(self):
        """ensure all nodes have 'migrate_allowed' in their stats output"""
        for node in self._nodes:
            node_stats = self._info_cmd_helper('statistics', node)
            allowed = node_stats['migrate_allowed']
            if allowed == "false":
                return False
        return True

    def _cluster_has_migs(self):
        """calls node_has_migs for each node"""
        migs = 0
        for node in self._nodes:
            if self._node_has_migs(node):
                migs += 1
        if migs == 0:
            return False
        return True

    def _has_migs(self, local):
        if local:
            return self._local_node_has_migs()
        return self._cluster_has_migs()

    def _local_node_has_migs(self):
        return self._node_has_migs(None)

    def _is_min_cluster_size(self):
        """checks that all nodes in the cluster are returning the
        mininimum cluster size specified in their statistics output"""
        sizes = set()
        for node in self._cluster_statistics:
            sizes.add(int(self._cluster_statistics[node]['cluster_size']))

        if (len(sizes)) > 1:  # if we are getting more than 1 size, lets say no
            return False
        if (min(sizes)) >= self.module.params['min_cluster_size']:
            return True
        return False

    def _cluster_stable(self):
        """Added 4.3:
        cluster-stable:size=<target-cluster-size>;ignore-migrations=<yes/no>;namespace=<namespace-name>
        Returns the current 'cluster_key' when the following are satisfied:

         If 'size' is specified then the target node's 'cluster-size'
         must match size.
         If 'ignore-migrations' is either unspecified or 'false' then
         the target node's migrations counts must be zero for the provided
         'namespace' or all namespaces if 'namespace' is not provided."""
        cluster_key = set()
        cluster_key.add(self._info_cmd_helper('statistics')['cluster_key'])
        cmd = "cluster-stable:"
        target_cluster_size = self.module.params['target_cluster_size']
        if target_cluster_size is not None:
            cmd = cmd + "size=" + str(target_cluster_size) + ";"
        for node in self._nodes:
            cluster_key.add(self._info_cmd_helper(cmd, node))
        if len(cluster_key) == 1:
            return True
        return False

    def _cluster_good_state(self):
        """checks a few things to make sure we're OK to say the cluster
        has no migs. It could be in a unhealthy condition that does not allow
        migs, or a split brain"""
        if self._cluster_key_consistent() is not True:
            return False, "Cluster key inconsistent."
        if self._is_min_cluster_size() is not True:
            return False, "Cluster min size not reached."
        if self._cluster_migrates_allowed() is not True:
            return False, "migrate_allowed is false somewhere."
        return True, "OK."

    def has_migs(self, local=True):
        """returns a boolean, False if no migrations otherwise True"""
        consecutive_good = 0
        try_num = 0
        skip_reason = list()
        while \
            try_num < int(self.module.params['tries_limit']) and \
                consecutive_good < \
                int(self.module.params['consecutive_good_checks']):

            self._update_nodes_list()
            self._update_cluster_statistics()

            # These checks are outside of the while loop because
            # we probably want to skip & sleep instead of failing entirely
            stable, reason = self._cluster_good_state()
            if stable is not True:
                skip_reason.append(
                    "Skipping on try#" + str(try_num) +
                    " for reason:" + reason
                )
            else:
                if self._can_use_cluster_stable():
                    if self._cluster_stable():
                        consecutive_good += 1
                    else:
                        consecutive_good = 0
                        skip_reason.append(
                            "Skipping on try#" + str(try_num) +
                            " for reason:" + " cluster_stable"
                        )
                elif self._has_migs(local):
                    # print("_has_migs")
                    skip_reason.append(
                        "Skipping on try#" + str(try_num) +
                        " for reason:" + " migrations"
                    )
                    consecutive_good = 0
                else:
                    consecutive_good += 1
                    if consecutive_good == self.module.params[
                            'consecutive_good_checks']:
                        break
            try_num += 1
            sleep(self.module.params['sleep_between_checks'])
            # print(skip_reason)
        if consecutive_good == self.module.params['consecutive_good_checks']:
            return False, None
        return True, skip_reason


def main():
    """main method for ansible module"""
    run_module()


if __name__ == '__main__':
    main()
