#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016-2017, Cumulus Networks <ce-ceng@cumulusnetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: nclu
version_added: "2.3"
author: "Cumulus Networks"
short_description: Configure network interfaces using NCLU
description:
    - Interface to the Network Command Line Utility, developed to make it easier
      to configure operating systems running ifupdown2 and Quagga, such as
      Cumulus Linux. Command documentation is available at
      U(https://docs.cumulusnetworks.com/display/DOCS/Network+Command+Line+Utility)
options:
    commands:
        description:
            - A list of strings containing the net commands to run. Mutually
              exclusive with I(template).
    template:
        description:
            - A single, multi-line string with jinja2 formatting. This string
              will be broken by lines, and each line will be run through net.
              Mutually exclusive with I(commands).
    commit:
        description:
            - When true, performs a 'net commit' at the end of the block.
              Mutually exclusive with I(atomic).
        default: false
    abort:
        description:
            - Boolean. When true, perform a 'net abort' before the block.
              This cleans out any uncommitted changes in the buffer.
              Mutually exclusive with I(atomic).
        default: false
    atomic:
        description:
            - When true, equivalent to both I(commit) and I(abort) being true.
              Mutually exclusive with I(commit) and I(atomic).
        default: false
    description:
        description:
            - Commit description that will be recorded to the commit log if
              I(commit) or I(atomic) are true.
        default: "Ansible-originated commit"
'''

EXAMPLES = '''

- name: Add two interfaces without committing any changes
  nclu:
    commands:
        - add int swp1
        - add int swp2

- name: Add 48 interfaces and commit the change.
  nclu:
    template: |
        {% for iface in range(1,49) %}
        add int swp{{iface}}
        {% endfor %}
    commit: true
    description: "Ansible - add swps1-48"

- name: Atomically add an interface
  nclu:
    commands:
        - add int swp1
    atomic: true
    description: "Ansible - add swp1"
'''

RETURN = '''
changed:
    description: whether the interface was changed
    returned: changed
    type: bool
    sample: True
msg:
    description: human-readable report of success or failure
    returned: always
    type: string
    sample: "interface bond0 config updated"
'''

from ansible.module_utils.basic import AnsibleModule


def command_helper(module, command, errmsg=None):
    """Run a command, catch any nclu errors"""
    (_rc, output, _err) = module.run_command("/usr/bin/net %s"%command)
    if _rc or 'ERROR' in output or 'ERROR' in _err:
        module.fail_json(msg=errmsg or output)
    return str(output)


def check_pending(module):
    """Check the pending diff of the nclu buffer."""
    pending = command_helper(module, "pending", "Error in pending config. You may want to view `net pending` on this target.")

    delimeter1 = "net add/del commands since the last 'net commit'"
    color1 = '\x1b[94m'
    if delimeter1 in pending:
        pending = pending.split(delimeter1)[0]
        pending = pending.replace(color1, '')
    return pending.strip()


def run_nclu(module, command_list, command_string, commit, atomic, abort, description):
    _changed = False

    commands = []
    if command_list:
        commands = command_list
    elif command_string:
        commands = command_string.splitlines()

    do_commit = False
    do_abort = abort
    if commit or atomic:
        do_commit = True
        if atomic:
            do_abort = True

    if do_abort:
        command_helper(module, "abort")

    # First, look at the staged commands.
    before = check_pending(module)
    # Run all of the the net commands
    output_lines = []
    for line in commands:
        output_lines += [command_helper(module, line.strip(), "Failed on line %s"%line)]
    output = "\n".join(output_lines)

    # If pending changes changed, report a change.
    after = check_pending(module)
    if before == after:
        _changed = False
    else:
        _changed = True

    # Do the commit.
    if do_commit:
        result = command_helper(module, "commit description '%s'"%description)
        if "commit ignored" in result:
            _changed = False
            command_helper(module, "abort")
        elif command_helper(module, "show commit last") == "":
            _changed = False

    return _changed, output


def main(testing=False):
    module = AnsibleModule(argument_spec=dict(
        commands = dict(required=False, type='list'),
        template = dict(required=False, type='str'),
        description = dict(required=False, type='str', default="Ansible-originated commit"),
        abort = dict(required=False, type='bool', default=False),
        commit = dict(required=False, type='bool', default=False),
        atomic = dict(required=False, type='bool', default=False)),
        mutually_exclusive=[('commands', 'template'),
                            ('commit', 'atomic'),
                            ('abort', 'atomic')]
    )
    command_list = module.params.get('commands', None)
    command_string = module.params.get('template', None)
    commit = module.params.get('commit')
    atomic = module.params.get('atomic')
    abort = module.params.get('abort')
    description = module.params.get('description')

    _changed, output = run_nclu(module, command_list, command_string, commit, atomic, abort, description)
    if not testing:
        module.exit_json(changed=_changed, msg=output)
    elif testing:
        return {"changed": _changed, "msg": output}


if __name__ == '__main__':
    main()
