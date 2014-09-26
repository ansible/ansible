#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
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

DOCUMENTATION = '''
---
module: setup
version_added: historical
short_description: Gathers facts about remote hosts
options:
    filter:
        version_added: "1.1"
        description:
            - if supplied, only return facts that match this shell-style (fnmatch) wildcard.
        required: false
        default: '*'
    fact_path:
        version_added: "1.3"
        description:
            - path used for local ansible facts (*.fact) - files in this dir
              will be run (if executable) and their results be added to ansible_local facts
              if a file is not executable it is read.
              File/results format can be json or ini-format
        required: false
        default: '/etc/ansible/facts.d'
description:
     - This module is automatically called by playbooks to gather useful
       variables about remote hosts that can be used in playbooks. It can also be
       executed directly by C(/usr/bin/ansible) to check what variables are
       available to a host. Ansible provides many I(facts) about the system,
       automatically.
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
      C(fact_path) or C(filter) as this is provided by a simpler implementation of the module.
      Different facts are returned for Windows hosts.
author: Michael DeHaan
'''

EXAMPLES = """
# Display facts from all hosts and store them indexed by I(hostname) at C(/tmp/facts).
ansible all -m setup --tree /tmp/facts

# Display only facts regarding memory found by ansible on all hosts and output them.
ansible all -m setup -a 'filter=ansible_*_mb'

# Display only facts returned by facter.
ansible all -m setup -a 'filter=facter_*'

# Display only facts about certain interfaces.
ansible all -m setup -a 'filter=ansible_eth[0-2]'
"""


def run_setup(module):

    setup_options = dict(module_setup=True)
    facts = ansible_facts(module)

    for (k, v) in facts.items():
        setup_options["ansible_%s" % k.replace('-', '_')] = v

    # Look for the path to the facter and ohai binary and set
    # the variable to that path.
    facter_path = module.get_bin_path('facter')
    ohai_path = module.get_bin_path('ohai')

    # if facter is installed, and we can use --json because
    # ruby-json is ALSO installed, include facter data in the JSON
    if facter_path is not None:
        rc, out, err = module.run_command(facter_path + " --puppet --json")
        facter = True
        try:
            facter_ds = json.loads(out)
        except:
            facter = False
        if facter:
            for (k,v) in facter_ds.items():
                setup_options["facter_%s" % k] = v

    # ditto for ohai
    if ohai_path is not None:
        rc, out, err = module.run_command(ohai_path)
        ohai = True
        try:
            ohai_ds = json.loads(out)
        except:
            ohai = False
        if ohai:
            for (k,v) in ohai_ds.items():
                k2 = "ohai_%s" % k.replace('-', '_')
                setup_options[k2] = v

    setup_result = { 'ansible_facts': {} }

    for (k,v) in setup_options.items():
        if module.params['filter'] == '*' or fnmatch.fnmatch(k, module.params['filter']):
            setup_result['ansible_facts'][k] = v

    # hack to keep --verbose from showing all the setup module results
    setup_result['verbose_override'] = True

    return setup_result

def main():
    global module
    module = AnsibleModule(
        argument_spec = dict(
            filter=dict(default="*", required=False),
            fact_path=dict(default='/etc/ansible/facts.d', required=False),
        ),
        supports_check_mode = True,
    )
    data = run_setup(module)
    module.exit_json(**data)

# import module snippets

from ansible.module_utils.basic import *

from ansible.module_utils.facts import *

main()
