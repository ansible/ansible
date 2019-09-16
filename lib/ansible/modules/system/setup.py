#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: setup
version_added: historical
short_description: Gathers facts about remote hosts
options:
    gather_subset:
        version_added: "2.1"
        description:
            - "if supplied, restrict the additional facts collected to the given subset.
              Possible values: C(all), C(min), C(hardware), C(network), C(virtual), C(ohai), and
              C(facter). Can specify a list of values to specify a larger subset.
              Values can also be used with an initial C(!) to specify that
              that specific subset should not be collected.  For instance:
              C(!hardware,!network,!virtual,!ohai,!facter). If C(!all) is specified
              then only the min subset is collected. To avoid collecting even the
              min subset, specify C(!all,!min). To collect only specific facts,
              use C(!all,!min), and specify the particular fact subsets.
              Use the filter parameter if you do not want to display some collected
              facts."
        required: false
        default: 'all'
    gather_timeout:
        version_added: "2.2"
        description:
            - "Set the default timeout in seconds for individual fact gathering"
        required: false
        default: 10
    filter:
        version_added: "1.1"
        description:
            - if supplied, only return facts that match this shell-style (fnmatch) wildcard.
        required: false
        default: '*'
    fact_path:
        version_added: "1.3"
        description:
            - path used for local ansible facts (C(*.fact)) - files in this dir
              will be run (if executable) and their results be added to C(ansible_local) facts
              if a file is not executable it is read. Check notes for Windows options. (from 2.1 on)
              File/results format can be JSON or INI-format. The default C(fact_path) can be
              specified in C(ansible.cfg) for when setup is automatically called as part of
              C(gather_facts).
        required: false
        default: '/etc/ansible/facts.d'
description:
     - This module is automatically called by playbooks to gather useful
       variables about remote hosts that can be used in playbooks. It can also be
       executed directly by C(/usr/bin/ansible) to check what variables are
       available to a host. Ansible provides many I(facts) about the system,
       automatically.
     - This module is also supported for Windows targets.
notes:
    - More ansible facts will be added with successive releases. If I(facter) or
      I(ohai) are installed, variables from these programs will also be snapshotted
      into the JSON file for usage in templating. These variables are prefixed
      with C(facter_) and C(ohai_) so it's easy to tell their source. All variables are
      bubbled up to the caller. Using the ansible facts and choosing to not
      install I(facter) and I(ohai) means you can avoid Ruby-dependencies on your
      remote systems. (See also M(facter) and M(ohai).)
    - The filter option filters only the first level subkey below ansible_facts.
    - If the target host is Windows, you will not currently have the ability to use
      C(filter) as this is provided by a simpler implementation of the module.
    - If the target host is Windows you can now use C(fact_path). Make sure that this path
      exists on the target host. Files in this path MUST be PowerShell scripts (``*.ps1``) and
      their output must be formattable in JSON (Ansible will take care of this). Test the
      output of your scripts.
      This option was added in Ansible 2.1.
    - This module is also supported for Windows targets.
    - This module should be run with elevated privileges on BSD systems to gather facts like ansible_product_version.
author:
    - "Ansible Core Team"
    - "Michael DeHaan"
    - "David O'Brien (@davidobrien1985)"
'''

EXAMPLES = """
# Display facts from all hosts and store them indexed by I(hostname) at C(/tmp/facts).
# ansible all -m setup --tree /tmp/facts

# Display only facts regarding memory found by ansible on all hosts and output them.
# ansible all -m setup -a 'filter=ansible_*_mb'

# Display only facts returned by facter.
# ansible all -m setup -a 'filter=facter_*'

# Collect only facts returned by facter.
# ansible all -m setup -a 'gather_subset=!all,!any,facter'

- name: Collect only facts returned by facter
  setup:
    gather_subset:
      - '!all'
      - '!any'
      - facter

# Display only facts about certain interfaces.
# ansible all -m setup -a 'filter=ansible_eth[0-2]'

# Restrict additional gathered facts to network and virtual (includes default minimum facts)
# ansible all -m setup -a 'gather_subset=network,virtual'

# Collect only network and virtual (excludes default minimum facts)
# ansible all -m setup -a 'gather_subset=!all,!any,network,virtual'

# Do not call puppet facter or ohai even if present.
# ansible all -m setup -a 'gather_subset=!facter,!ohai'

# Only collect the default minimum amount of facts:
# ansible all -m setup -a 'gather_subset=!all'

# Collect no facts, even the default minimum subset of facts:
# ansible all -m setup -a 'gather_subset=!all,!min'

# Display facts from Windows hosts with custom facts stored in C(C:\\custom_facts).
# ansible windows -m setup -a "fact_path='c:\\custom_facts'"
"""

# import module snippets
from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.facts.namespace import PrefixFactNamespace
from ansible.module_utils.facts import ansible_collector

from ansible.module_utils.facts import default_collectors


def main():
    module = AnsibleModule(
        argument_spec=dict(
            gather_subset=dict(default=["all"], required=False, type='list'),
            gather_timeout=dict(default=10, required=False, type='int'),
            filter=dict(default="*", required=False),
            fact_path=dict(default='/etc/ansible/facts.d', required=False, type='path'),
        ),
        supports_check_mode=True,
    )

    gather_subset = module.params['gather_subset']
    gather_timeout = module.params['gather_timeout']
    filter_spec = module.params['filter']

    # TODO: this mimics existing behavior where gather_subset=["!all"] actually means
    #       to collect nothing except for the below list
    # TODO: decide what '!all' means, I lean towards making it mean none, but likely needs
    #       some tweaking on how gather_subset operations are performed
    minimal_gather_subset = frozenset(['apparmor', 'caps', 'cmdline', 'date_time',
                                       'distribution', 'dns', 'env', 'fips', 'local',
                                       'lsb', 'pkg_mgr', 'platform', 'python', 'selinux',
                                       'service_mgr', 'ssh_pub_keys', 'user'])

    all_collector_classes = default_collectors.collectors

    # rename namespace_name to root_key?
    namespace = PrefixFactNamespace(namespace_name='ansible',
                                    prefix='ansible_')

    fact_collector = \
        ansible_collector.get_ansible_collector(all_collector_classes=all_collector_classes,
                                                namespace=namespace,
                                                filter_spec=filter_spec,
                                                gather_subset=gather_subset,
                                                gather_timeout=gather_timeout,
                                                minimal_gather_subset=minimal_gather_subset)

    facts_dict = fact_collector.collect(module=module)

    module.exit_json(ansible_facts=facts_dict)


if __name__ == '__main__':
    main()
