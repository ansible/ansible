#!/usr/bin/python
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
#

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "network",
}


DOCUMENTATION = """module: ios_config
author: Peter Sprygada (@privateip)
short_description: Manage Cisco IOS configuration sections
description:
- Cisco IOS configurations use a simple block indent file syntax for segmenting configuration
  into sections.  This module provides an implementation for working with IOS configuration
  sections in a deterministic way.
extends_documentation_fragment:
- cisco.ios.ios
notes:
- Tested against IOS 15.6
- Abbreviated commands are NOT idempotent, see L(Network FAQ,../network/user_guide/faq.html#why-do-the-config-modules-always-return-changed-true-with-abbreviated-commands).
options:
  lines:
    description:
    - The ordered set of commands that should be configured in the section.  The commands
      must be the exact same commands as found in the device running-config.  Be sure
      to note the configuration command syntax as some commands are automatically
      modified by the device config parser.
    aliases:
    - commands
  parents:
    description:
    - The ordered set of parents that uniquely identify the section or hierarchy the
      commands should be checked against.  If the parents argument is omitted, the
      commands are checked against the set of top level or global commands.
  src:
    description:
    - Specifies the source path to the file that contains the configuration or configuration
      template to load.  The path to the source file can either be the full path on
      the Ansible control host or a relative path from the playbook or role root directory.  This
      argument is mutually exclusive with I(lines), I(parents).
  before:
    description:
    - The ordered set of commands to push on to the command stack if a change needs
      to be made.  This allows the playbook designer the opportunity to perform configuration
      commands prior to pushing any changes without affecting how the set of commands
      are matched against the system.
  after:
    description:
    - The ordered set of commands to append to the end of the command stack if a change
      needs to be made.  Just like with I(before) this allows the playbook designer
      to append a set of commands to be executed after the command set.
  match:
    description:
    - Instructs the module on the way to perform the matching of the set of commands
      against the current device config.  If match is set to I(line), commands are
      matched line by line.  If match is set to I(strict), command lines are matched
      with respect to position.  If match is set to I(exact), command lines must be
      an equal match.  Finally, if match is set to I(none), the module will not attempt
      to compare the source configuration with the running configuration on the remote
      device.
    choices:
    - line
    - strict
    - exact
    - none
    default: line
  replace:
    description:
    - Instructs the module on the way to perform the configuration on the device.
      If the replace argument is set to I(line) then the modified lines are pushed
      to the device in configuration mode.  If the replace argument is set to I(block)
      then the entire command block is pushed to the device in configuration mode
      if any line is not correct.
    default: line
    choices:
    - line
    - block
  multiline_delimiter:
    description:
    - This argument is used when pushing a multiline configuration element to the
      IOS device.  It specifies the character to use as the delimiting character.  This
      only applies to the configuration action.
    default: '@'
  backup:
    description:
    - This argument will cause the module to create a full backup of the current C(running-config)
      from the remote device before any changes are made. If the C(backup_options)
      value is not given, the backup file is written to the C(backup) folder in the
      playbook root directory or role root directory, if playbook is part of an ansible
      role. If the directory does not exist, it is created.
    type: bool
    default: 'no'
  running_config:
    description:
    - The module, by default, will connect to the remote device and retrieve the current
      running-config to use as a base for comparing against the contents of source.
      There are times when it is not desirable to have the task get the current running-config
      for every task in a playbook.  The I(running_config) argument allows the implementer
      to pass in the configuration to use as the base config for comparison.
    aliases:
    - config
  defaults:
    description:
    - This argument specifies whether or not to collect all defaults when getting
      the remote device running config.  When enabled, the module will get the current
      config by issuing the command C(show running-config all).
    type: bool
    default: 'no'
  save_when:
    description:
    - When changes are made to the device running-configuration, the changes are not
      copied to non-volatile storage by default.  Using this argument will change
      that before.  If the argument is set to I(always), then the running-config will
      always be copied to the startup-config and the I(modified) flag will always
      be set to True.  If the argument is set to I(modified), then the running-config
      will only be copied to the startup-config if it has changed since the last save
      to startup-config.  If the argument is set to I(never), the running-config will
      never be copied to the startup-config.  If the argument is set to I(changed),
      then the running-config will only be copied to the startup-config if the task
      has made a change. I(changed) was added in Ansible 2.5.
    default: never
    choices:
    - always
    - never
    - modified
    - changed
  diff_against:
    description:
    - When using the C(ansible-playbook --diff) command line argument the module can
      generate diffs against different sources.
    - When this option is configure as I(startup), the module will return the diff
      of the running-config against the startup-config.
    - When this option is configured as I(intended), the module will return the diff
      of the running-config against the configuration provided in the C(intended_config)
      argument.
    - When this option is configured as I(running), the module will return the before
      and after diff of the running-config with respect to any changes made to the
      device configuration.
    choices:
    - running
    - startup
    - intended
  diff_ignore_lines:
    description:
    - Use this argument to specify one or more lines that should be ignored during
      the diff.  This is used for lines in the configuration that are automatically
      updated by the system.  This argument takes a list of regular expressions or
      exact line matches.
  intended_config:
    description:
    - The C(intended_config) provides the master configuration that the node should
      conform to and is used to check the final running-config against. This argument
      will not modify any settings on the remote device and is strictly used to check
      the compliance of the current device's configuration against.  When specifying
      this argument, the task should also modify the C(diff_against) value and set
      it to I(intended).
  backup_options:
    description:
    - This is a dict object containing configurable options related to backup file
      path. The value of this option is read only when C(backup) is set to I(yes),
      if C(backup) is set to I(no) this option will be silently ignored.
    suboptions:
      filename:
        description:
        - The filename to be used to store the backup configuration. If the filename
          is not given it will be generated based on the hostname, current time and
          date in format defined by <hostname>_config.<current-date>@<current-time>
      dir_path:
        description:
        - This option provides the path ending with directory name in which the backup
          configuration file will be stored. If the directory does not exist it will
          be first created and the filename is either the value of C(filename) or
          default filename as described in C(filename) options description. If the
          path value is not given in that case a I(backup) directory will be created
          in the current working directory and backup configuration will be copied
          in C(filename) within I(backup) directory.
        type: path
    type: dict
"""

EXAMPLES = """
- name: configure top level configuration
  ios_config:
    lines: hostname {{ inventory_hostname }}

- name: configure interface settings
  ios_config:
    lines:
      - description test interface
      - ip address 172.31.1.1 255.255.255.0
    parents: interface Ethernet1

- name: configure ip helpers on multiple interfaces
  ios_config:
    lines:
      - ip helper-address 172.26.1.10
      - ip helper-address 172.26.3.8
    parents: "{{ item }}"
  with_items:
    - interface Ethernet1
    - interface Ethernet2
    - interface GigabitEthernet1

- name: configure policer in Scavenger class
  ios_config:
    lines:
      - conform-action transmit
      - exceed-action drop
    parents:
      - policy-map Foo
      - class Scavenger
      - police cir 64000

- name: load new acl into device
  ios_config:
    lines:
      - 10 permit ip host 192.0.2.1 any log
      - 20 permit ip host 192.0.2.2 any log
      - 30 permit ip host 192.0.2.3 any log
      - 40 permit ip host 192.0.2.4 any log
      - 50 permit ip host 192.0.2.5 any log
    parents: ip access-list extended test
    before: no ip access-list extended test
    match: exact

- name: check the running-config against master config
  ios_config:
    diff_against: intended
    intended_config: "{{ lookup('file', 'master.cfg') }}"

- name: check the startup-config against the running-config
  ios_config:
    diff_against: startup
    diff_ignore_lines:
      - ntp clock .*

- name: save running to startup when modified
  ios_config:
    save_when: modified

- name: for idempotency, use full-form commands
  ios_config:
    lines:
      # - shut
      - shutdown
    # parents: int gig1/0/11
    parents: interface GigabitEthernet1/0/11

# Set boot image based on comparison to a group_var (version) and the version
# that is returned from the `ios_facts` module
- name: SETTING BOOT IMAGE
  ios_config:
    lines:
      - no boot system
      - boot system flash bootflash:{{new_image}}
    host: "{{ inventory_hostname }}"
  when: ansible_net_version != version

- name: render a Jinja2 template onto an IOS device
  ios_config:
    backup: yes
    src: ios_template.j2

- name: configurable backup path
  ios_config:
    src: ios_template.j2
    backup: yes
    backup_options:
      filename: backup.cfg
      dir_path: /home/user
"""

RETURN = """
updates:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['hostname foo', 'router ospf 1', 'router-id 192.0.2.1']
commands:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['hostname foo', 'router ospf 1', 'router-id 192.0.2.1']
backup_path:
  description: The full path to the backup file
  returned: when backup is yes
  type: str
  sample: /playbooks/ansible/backup/ios_config.2016-07-16@22:28:34
filename:
  description: The name of the backup file
  returned: when backup is yes and filename is not specified in backup options
  type: str
  sample: ios_config.2016-07-16@22:28:34
shortname:
  description: The full path to the backup file excluding the timestamp
  returned: when backup is yes and filename is not specified in backup options
  type: str
  sample: /playbooks/ansible/backup/ios_config
date:
  description: The date extracted from the backup file name
  returned: when backup is yes
  type: str
  sample: "2016-07-16"
time:
  description: The time extracted from the backup file name
  returned: when backup is yes
  type: str
  sample: "22:28:34"
"""
import json

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import ConnectionError
from ansible_collections.cisco.ios.plugins.module_utils.network.ios.ios import (
    run_commands,
    get_config,
)
from ansible_collections.cisco.ios.plugins.module_utils.network.ios.ios import (
    get_defaults_flag,
    get_connection,
)
from ansible_collections.cisco.ios.plugins.module_utils.network.ios.ios import (
    ios_argument_spec,
)
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.config import (
    NetworkConfig,
    dumps,
)


def check_args(module, warnings):
    if module.params["multiline_delimiter"]:
        if len(module.params["multiline_delimiter"]) != 1:
            module.fail_json(
                msg="multiline_delimiter value can only be a "
                "single character"
            )


def edit_config_or_macro(connection, commands):
    # only catch the macro configuration command,
    # not negated 'no' variation.
    if commands[0].startswith("macro name"):
        connection.edit_macro(candidate=commands)
    else:
        connection.edit_config(candidate=commands)


def get_candidate_config(module):
    candidate = ""
    if module.params["src"]:
        candidate = module.params["src"]

    elif module.params["lines"]:
        candidate_obj = NetworkConfig(indent=1)
        parents = module.params["parents"] or list()
        candidate_obj.add(module.params["lines"], parents=parents)
        candidate = dumps(candidate_obj, "raw")

    return candidate


def get_running_config(module, current_config=None, flags=None):
    running = module.params["running_config"]
    if not running:
        if not module.params["defaults"] and current_config:
            running = current_config
        else:
            running = get_config(module, flags=flags)

    return running


def save_config(module, result):
    result["changed"] = True
    if not module.check_mode:
        run_commands(module, "copy running-config startup-config\r")
    else:
        module.warn(
            "Skipping command `copy running-config startup-config` "
            "due to check_mode.  Configuration not copied to "
            "non-volatile storage"
        )


def main():
    """ main entry point for module execution
    """
    backup_spec = dict(filename=dict(), dir_path=dict(type="path"))
    argument_spec = dict(
        src=dict(type="path"),
        lines=dict(aliases=["commands"], type="list"),
        parents=dict(type="list"),
        before=dict(type="list"),
        after=dict(type="list"),
        match=dict(
            default="line", choices=["line", "strict", "exact", "none"]
        ),
        replace=dict(default="line", choices=["line", "block"]),
        multiline_delimiter=dict(default="@"),
        running_config=dict(aliases=["config"]),
        intended_config=dict(),
        defaults=dict(type="bool", default=False),
        backup=dict(type="bool", default=False),
        backup_options=dict(type="dict", options=backup_spec),
        save_when=dict(
            choices=["always", "never", "modified", "changed"], default="never"
        ),
        diff_against=dict(choices=["startup", "intended", "running"]),
        diff_ignore_lines=dict(type="list"),
    )

    argument_spec.update(ios_argument_spec)

    mutually_exclusive = [("lines", "src"), ("parents", "src")]

    required_if = [
        ("match", "strict", ["lines"]),
        ("match", "exact", ["lines"]),
        ("replace", "block", ["lines"]),
        ("diff_against", "intended", ["intended_config"]),
    ]

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=mutually_exclusive,
        required_if=required_if,
        supports_check_mode=True,
    )

    result = {"changed": False}

    warnings = list()
    check_args(module, warnings)
    result["warnings"] = warnings

    diff_ignore_lines = module.params["diff_ignore_lines"]
    config = None
    contents = None
    flags = get_defaults_flag(module) if module.params["defaults"] else []
    connection = get_connection(module)

    if module.params["backup"] or (
        module._diff and module.params["diff_against"] == "running"
    ):
        contents = get_config(module, flags=flags)
        config = NetworkConfig(indent=1, contents=contents)
        if module.params["backup"]:
            result["__backup__"] = contents

    if any((module.params["lines"], module.params["src"])):
        match = module.params["match"]
        replace = module.params["replace"]
        path = module.params["parents"]

        candidate = get_candidate_config(module)
        running = get_running_config(module, contents, flags=flags)
        try:
            response = connection.get_diff(
                candidate=candidate,
                running=running,
                diff_match=match,
                diff_ignore_lines=diff_ignore_lines,
                path=path,
                diff_replace=replace,
            )
        except ConnectionError as exc:
            module.fail_json(msg=to_text(exc, errors="surrogate_then_replace"))

        config_diff = response["config_diff"]
        banner_diff = response["banner_diff"]

        if config_diff or banner_diff:
            commands = config_diff.split("\n")

            if module.params["before"]:
                commands[:0] = module.params["before"]

            if module.params["after"]:
                commands.extend(module.params["after"])

            result["commands"] = commands
            result["updates"] = commands
            result["banners"] = banner_diff

            # send the configuration commands to the device and merge
            # them with the current running config
            if not module.check_mode:
                if commands:
                    edit_config_or_macro(connection, commands)
                if banner_diff:
                    connection.edit_banner(
                        candidate=json.dumps(banner_diff),
                        multiline_delimiter=module.params[
                            "multiline_delimiter"
                        ],
                    )

            result["changed"] = True

    running_config = module.params["running_config"]
    startup_config = None

    if module.params["save_when"] == "always":
        save_config(module, result)
    elif module.params["save_when"] == "modified":
        output = run_commands(
            module, ["show running-config", "show startup-config"]
        )

        running_config = NetworkConfig(
            indent=1, contents=output[0], ignore_lines=diff_ignore_lines
        )
        startup_config = NetworkConfig(
            indent=1, contents=output[1], ignore_lines=diff_ignore_lines
        )

        if running_config.sha1 != startup_config.sha1:
            save_config(module, result)
    elif module.params["save_when"] == "changed" and result["changed"]:
        save_config(module, result)

    if module._diff:
        if not running_config:
            output = run_commands(module, "show running-config")
            contents = output[0]
        else:
            contents = running_config

        # recreate the object in order to process diff_ignore_lines
        running_config = NetworkConfig(
            indent=1, contents=contents, ignore_lines=diff_ignore_lines
        )

        if module.params["diff_against"] == "running":
            if module.check_mode:
                module.warn(
                    "unable to perform diff against running-config due to check mode"
                )
                contents = None
            else:
                contents = config.config_text

        elif module.params["diff_against"] == "startup":
            if not startup_config:
                output = run_commands(module, "show startup-config")
                contents = output[0]
            else:
                contents = startup_config.config_text

        elif module.params["diff_against"] == "intended":
            contents = module.params["intended_config"]

        if contents is not None:
            base_config = NetworkConfig(
                indent=1, contents=contents, ignore_lines=diff_ignore_lines
            )

            if running_config.sha1 != base_config.sha1:
                if module.params["diff_against"] == "intended":
                    before = running_config
                    after = base_config
                elif module.params["diff_against"] in ("startup", "running"):
                    before = base_config
                    after = running_config

                result.update(
                    {
                        "changed": True,
                        "diff": {"before": str(before), "after": str(after)},
                    }
                )

    module.exit_json(**result)


if __name__ == "__main__":
    main()
