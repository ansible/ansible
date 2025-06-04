# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = """
---
module: setup
version_added: historical
short_description: Gathers facts about remote hosts
options:
    gather_subset:
        version_added: "2.1"
        description:
            - "If supplied, restrict the additional facts collected to the given subset.
              Possible values: V(all), V(all_ipv4_addresses), V(all_ipv6_addresses), V(apparmor), V(architecture),
              V(caps), V(chroot),V(cmdline), V(date_time), V(default_ipv4), V(default_ipv6), V(devices),
              V(distribution), V(distribution_major_version), V(distribution_release), V(distribution_version),
              V(dns), V(effective_group_ids), V(effective_user_id), V(env), V(facter), V(fips), V(hardware),
              V(interfaces), V(is_chroot), V(iscsi), V(kernel), V(local), V(lsb), V(machine), V(machine_id),
              V(mounts), V(network), V(ohai), V(os_family), V(pkg_mgr), V(platform), V(processor), V(processor_cores),
              V(processor_count), V(python), V(python_version), V(real_user_id), V(selinux), V(service_mgr),
              V(ssh_host_key_dsa_public), V(ssh_host_key_ecdsa_public), V(ssh_host_key_ed25519_public),
              V(ssh_host_key_rsa_public), V(ssh_host_pub_keys), V(ssh_pub_keys), V(system), V(system_capabilities),
              V(system_capabilities_enforced), V(systemd), V(user), V(user_dir), V(user_gecos), V(user_gid), V(user_id),
              V(user_shell), V(user_uid), V(virtual), V(virtualization_role), V(virtualization_type).
              Can specify a list of values to specify a larger subset.
              Values can also be used with an initial C(!) to specify that
              that specific subset should not be collected.  For instance:
              V(!hardware,!network,!virtual,!ohai,!facter). If V(!all) is specified
              then only the min subset is collected. To avoid collecting even the
              min subset, specify V(!all,!min). To collect only specific facts,
              use V(!all,!min), and specify the particular fact subsets.
              Use the filter parameter if you do not want to display some collected
              facts."
        type: list
        elements: str
        default: "all"
    gather_timeout:
        version_added: "2.2"
        description:
            - Set the default timeout in seconds for individual fact gathering.
        type: int
        default: 10
    filter:
        version_added: "1.1"
        description:
            - If supplied, only return facts that match one of the shell-style
              (fnmatch) pattern. An empty list basically means 'no filter'.
              As of Ansible 2.11, the type has changed from string to list
              and the default has became an empty list. A simple string is
              still accepted and works as a single pattern. The behaviour
              prior to Ansible 2.11 remains.
        type: list
        elements: str
        default: []
    fact_path:
        version_added: "1.3"
        description:
            - Path used for local ansible facts (C(*.fact)) - files in this dir
              will be run (if executable) and their results be added to C(ansible_local) facts.
              If a file is not executable it is read instead.
              File/results format can be JSON or INI-format. The default O(fact_path) can be
              specified in C(ansible.cfg) for when setup is automatically called as part of
              C(gather_facts).
              NOTE - For windows clients, the results will be added to a variable named after the
              local file (without extension suffix), rather than C(ansible_local).
            - Since Ansible 2.1, Windows hosts can use O(fact_path). Make sure that this path
              exists on the target host. Files in this path MUST be PowerShell scripts C(.ps1)
              which outputs an object. This object will be formatted by Ansible as json so the
              script should be outputting a raw hashtable, array, or other primitive object.
        type: path
        default: /etc/ansible/facts.d
description:
    - This module is automatically called by playbooks to gather useful
      variables about remote hosts that can be used in playbooks. It can also be
      executed directly by C(/usr/bin/ansible) to check what variables are
      available to a host. Ansible provides many I(facts) about the system,
      automatically.
    - This module is also supported for Windows targets.
extends_documentation_fragment:
  -  action_common_attributes
  -  action_common_attributes.facts
attributes:
    check_mode:
        support: full
    diff_mode:
        support: none
    facts:
        support: full
    platform:
        platforms: posix, windows
notes:
    - More ansible facts will be added with successive releases. If I(facter) or
      I(ohai) are installed, variables from these programs will also be snapshotted
      into the JSON file for usage in templating. These variables are prefixed
      with C(facter_) and C(ohai_) so it's easy to tell their source. All variables are
      bubbled up to the caller. Using the ansible facts and choosing to not
      install I(facter) and I(ohai) means you can avoid Ruby-dependencies on your
      remote systems. (See also M(community.general.facter) and M(community.general.ohai).)
    - The filter option filters only the first level subkey below ansible_facts.
    - If the target host is Windows, you will not currently have the ability to use
      O(filter) as this is provided by a simpler implementation of the module.
    - This module should be run with elevated privileges on BSD systems to gather facts like ansible_product_version.
    - For more information about delegated facts,
      please check U(https://docs.ansible.com/ansible/latest/user_guide/playbooks_delegation.html#delegating-facts).
author:
    - "Ansible Core Team"
    - "Michael DeHaan"
"""

EXAMPLES = r"""
# Display facts from all hosts and store them indexed by `hostname` at `/tmp/facts`.
# ansible all -m ansible.builtin.setup --tree /tmp/facts

# Display only facts regarding memory found by ansible on all hosts and output them.
# ansible all -m ansible.builtin.setup -a 'filter=ansible_*_mb'

# Display only facts returned by facter.
# ansible all -m ansible.builtin.setup -a 'filter=facter_*'

# Collect only facts returned by facter.
# ansible all -m ansible.builtin.setup -a 'gather_subset=!all,facter'

- name: Collect only facts returned by facter
  ansible.builtin.setup:
    gather_subset:
      - '!all'
      - '!<any valid subset>'
      - facter

- name: Filter and return only selected facts
  ansible.builtin.setup:
    filter:
      - 'ansible_distribution'
      - 'ansible_machine_id'
      - 'ansible_*_mb'

# Display only facts about certain interfaces.
# ansible all -m ansible.builtin.setup -a 'filter=ansible_eth[0-2]'

# Restrict additional gathered facts to network and virtual (includes default minimum facts)
# ansible all -m ansible.builtin.setup -a 'gather_subset=network,virtual'

# Collect only network and virtual (excludes default minimum facts)
# ansible all -m ansible.builtin.setup -a 'gather_subset=!all,network,virtual'

# Do not call puppet facter or ohai even if present.
# ansible all -m ansible.builtin.setup -a 'gather_subset=!facter,!ohai'

# Only collect the default minimum amount of facts:
# ansible all -m ansible.builtin.setup -a 'gather_subset=!all'

# Collect no facts, even the default minimum subset of facts:
# ansible all -m ansible.builtin.setup -a 'gather_subset=!all,!min'

# Display facts from Windows hosts with custom facts stored in C:\custom_facts.
# ansible windows -m ansible.builtin.setup -a "fact_path='c:\custom_facts'"

# Gathers facts for the machines in the dbservers group (a.k.a Delegating facts)
- hosts: app_servers
  tasks:
    - name: Gather facts from db servers
      ansible.builtin.setup:
      delegate_to: "{{ item }}"
      delegate_facts: true
      loop: "{{ groups['dbservers'] }}"
"""

# import module snippets
from ..module_utils.basic import AnsibleModule

from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.facts import ansible_collector, default_collectors
from ansible.module_utils.facts.collector import CollectorNotFoundError, CycleFoundInFactDeps, UnresolvedFactDep
from ansible.module_utils.facts.namespace import PrefixFactNamespace


def main():
    module = AnsibleModule(
        argument_spec=dict(
            gather_subset=dict(default=["all"], required=False, type='list', elements='str'),
            gather_timeout=dict(default=10, required=False, type='int'),
            filter=dict(default=[], required=False, type='list', elements='str'),
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

    try:
        fact_collector = ansible_collector.get_ansible_collector(all_collector_classes=all_collector_classes,
                                                                 namespace=namespace,
                                                                 filter_spec=filter_spec,
                                                                 gather_subset=gather_subset,
                                                                 gather_timeout=gather_timeout,
                                                                 minimal_gather_subset=minimal_gather_subset)
    except (TypeError, CollectorNotFoundError, CycleFoundInFactDeps, UnresolvedFactDep) as e:
        # bad subset given, collector, idk, deps declared but not found
        module.fail_json(msg=to_text(e))

    facts_dict = fact_collector.collect(module=module)

    module.exit_json(ansible_facts=facts_dict)


if __name__ == '__main__':
    main()
