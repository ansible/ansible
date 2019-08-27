#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_imish_config
short_description: Manage BIG-IP advanced routing configuration sections
description:
  - This module provides an implementation for working with advanced routing
    configuration sections in a deterministic way.
version_added: 2.8
options:
  route_domain:
    description:
      - Route domain to manage BGP configuration on.
    type: str
    default: 0
  lines:
    description:
      - The ordered set of commands that should be configured in the
        section.
      - The commands must be the exact same commands as found in the device
        running-config.
      - Be sure to note the configuration command syntax as some commands
        are automatically modified by the device config parser.
    type: list
    aliases: ['commands']
  parents:
    description:
      - The ordered set of parents that uniquely identify the section or hierarchy
        the commands should be checked against.
      - If the C(parents) argument is omitted, the commands are checked against
        the set of top level or global commands.
    type: list
  src:
    description:
      - The I(src) argument provides a path to the configuration file
        to load into the remote system.
      - The path can either be a full system path to the configuration
        file if the value starts with / or relative to the root of the
        implemented role or playbook.
      - This argument is mutually exclusive with the I(lines) and
        I(parents) arguments.
    type: path
  before:
    description:
      - The ordered set of commands to push on to the command stack if
        a change needs to be made.
      - This allows the playbook designer the opportunity to perform
        configuration commands prior to pushing any changes without
        affecting how the set of commands are matched against the system.
    type: list
  after:
    description:
      - The ordered set of commands to append to the end of the command
        stack if a change needs to be made.
      - Just like with I(before) this allows the playbook designer to
        append a set of commands to be executed after the command set.
    type: list
  match:
    description:
      - Instructs the module on the way to perform the matching of
        the set of commands against the current device config.
      - If match is set to I(line), commands are matched line by line.
      - If match is set to I(strict), command lines are matched with respect
        to position.
      - If match is set to I(exact), command lines must be an equal match.
      - Finally, if match is set to I(none), the module will not attempt to
        compare the source configuration with the running configuration on
        the remote device.
    type: str
    choices:
      - line
      - strict
      - exact
      - none
    default: line
  replace:
    description:
      - Instructs the module on the way to perform the configuration
        on the device.
      - If the replace argument is set to I(line) then the modified lines
        are pushed to the device in configuration mode.
      - If the replace argument is set to I(block) then the entire
        command block is pushed to the device in configuration mode if any
        line is not correct.
    type: str
    choices:
      - line
      - block
    default: line
  backup:
    description:
      - This argument will cause the module to create a full backup of
        the current C(running-config) from the remote device before any
        changes are made.
      - The backup file is written to the C(backup) folder in the playbook
        root directory or role root directory, if playbook is part of an
        ansible role. If the directory does not exist, it is created.
    type: bool
    default: 'no'
  running_config:
    description:
      - The module, by default, will connect to the remote device and
        retrieve the current running-config to use as a base for comparing
        against the contents of source.
      - There are times when it is not desirable to have the task get the
        current running-config for every task in a playbook.
      - The I(running_config) argument allows the implementer to pass in
        the configuration to use as the base config for comparison.
    type: str
    aliases: ['config']
  save_when:
    description:
      - When changes are made to the device running-configuration, the
        changes are not copied to non-volatile storage by default.
      - If the argument is set to I(always), then the running-config will
        always be copied to the startup-config and the I(modified) flag will
        always be set to C(True).
      - If the argument is set to I(modified), then the running-config
        will only be copied to the startup-config if it has changed since
        the last save to startup-config.
      - If the argument is set to I(never), the running-config will never be
        copied to the startup-config.
      - If the argument is set to I(changed), then the running-config
        will only be copied to the startup-config if the task has made a change.
    type: str
    choices:
      - always
      - never
      - modified
      - changed
    default: never
  diff_against:
    description:
      - When using the C(ansible-playbook --diff) command line argument
        the module can generate diffs against different sources.
      - When this option is configure as I(startup), the module will return
        the diff of the running-config against the startup-config.
      - When this option is configured as I(intended), the module will
        return the diff of the running-config against the configuration
        provided in the C(intended_config) argument.
      - When this option is configured as I(running), the module will
        return the before and after diff of the running-config with respect
        to any changes made to the device configuration.
    type: str
    choices:
      - startup
      - intended
      - running
    default: startup
  diff_ignore_lines:
    description:
      - Use this argument to specify one or more lines that should be
        ignored during the diff.
      - This is used for lines in the configuration that are automatically
        updated by the system.
      - This argument takes a list of regular expressions or exact line matches.
    type: list
  intended_config:
    description:
      - The C(intended_config) provides the master configuration that
        the node should conform to and is used to check the final
        running-config against.
      - This argument will not modify any settings on the remote device and
        is strictly used to check the compliance of the current device's
        configuration against.
      - When specifying this argument, the task should also modify the
        C(diff_against) value and set it to I(intended).
    type: str
  backup_options:
    description:
      - This is a dict object containing configurable options related to backup file path.
        The value of this option is read only when C(backup) is set to I(yes), if C(backup) is set
        to I(no) this option will be silently ignored.
    suboptions:
      filename:
        description:
          - The filename to be used to store the backup configuration. If the the filename
            is not given it will be generated based on the hostname, current time and date
            in format defined by <hostname>_config.<current-date>@<current-time>
        type: str
      dir_path:
        description:
          - This option provides the path ending with directory name in which the backup
            configuration file will be stored. If the directory does not exist it will be first
            created and the filename is either the value of C(filename) or default filename
            as described in C(filename) options description. If the path value is not given
            in that case a I(backup) directory will be created in the current working directory
            and backup configuration will be copied in C(filename) within I(backup) directory.
        type: path
    type: dict
    version_added: "2.8"
notes:
  - Abbreviated commands are NOT idempotent, see
    L(Network FAQ,../network/user_guide/faq.html#why-do-the-config-modules-always-return-changed-true-with-abbreviated-commands).
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: configure top level configuration and save it
  bigip_imish_config:
    lines: bfd slow-timer 2000
    save_when: modified
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost

- name: diff the running-config against a provided config
  bigip_imish_config:
    diff_against: intended
    intended_config: "{{ lookup('file', 'master.cfg') }}"
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost

- name: Add config to a parent block
  bigip_imish_config:
    lines:
      - bgp graceful-restart restart-time 120
      - redistribute kernel route-map rhi
      - neighbor 10.10.10.11 remote-as 65000
      - neighbor 10.10.10.11 fall-over bfd
      - neighbor 10.10.10.11 remote-as 65000
      - neighbor 10.10.10.11 fall-over bfd
    parents: router bgp 64664
    match: exact
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost

- name: Remove an existing acl before writing it
  bigip_imish_config:
    lines:
      - access-list 10 permit 20.20.20.20
      - access-list 10 permit 20.20.20.21
      - access-list 10 deny any
    before: no access-list 10
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost

- name: for idempotency, use full-form commands
  bigip_imish_config:
    lines:
      # - desc My interface
      - description My Interface
    # parents: int ANYCAST-P2P-2
    parents: interface ANYCAST-P2P-2
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost

- name: configurable backup path
  bigip_imish_config:
    lines: bfd slow-timer 2000
    backup: yes
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
    backup_options:
      filename: backup.cfg
      dir_path: /home/user
  delegate_to: localhost
'''

RETURN = r'''
commands:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['interface ANYCAST-P2P-2', 'neighbor 20.20.20.21 remote-as 65000', 'neighbor 20.20.20.21 fall-over bfd']
updates:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['interface ANYCAST-P2P-2', 'neighbor 20.20.20.21 remote-as 65000', 'neighbor 20.20.20.21 fall-over bfd']
backup_path:
  description: The full path to the backup file
  returned: when backup is yes
  type: str
  sample: /playbooks/ansible/backup/bigip_imish_config.2016-07-16@22:28:34
'''


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


import os
import tempfile

from ansible.module_utils.network.common.config import NetworkConfig, dumps
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.icontrol import upload_file
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.icontrol import upload_file


class Parameters(AnsibleF5Parameters):
    api_map = {

    }

    api_attributes = [

    ]

    returnables = [
        '__backup__',
        'commands',
        'updates'
    ]

    updatables = [

    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    pass


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class UsableChanges(Changes):
    pass


class ReportableChanges(Changes):
    pass


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            return self.__default(param)

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(params=changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = Parameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                if isinstance(change, dict):
                    changed.update(change)
                else:
                    changed[k] = change
        if changed:
            self.changes = UsableChanges(params=changed)
            return True
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def exec_module(self):
        result = dict()
        changed = self.present()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        return result

    def present(self):
        result = dict(changed=False)
        config = None
        contents = None

        if self.want.backup or (self.module._diff and self.want.diff_against == 'running'):
            contents = self.read_current_from_device()
            config = NetworkConfig(indent=1, contents=contents)
            if self.want.backup:
                # The backup file is created in the bigip_imish_config action plugin. Refer
                # to that if you have questions. The key below is removed by the action plugin.
                result['__backup__'] = contents

        if any((self.want.src, self.want.lines)):
            match = self.want.match
            replace = self.want.replace

            candidate = self.get_candidate()
            running = self.get_running_config(contents)

            response = self.get_diff(
                candidate=candidate,
                running=running,
                diff_match=match,
                diff_ignore_lines=self.want.diff_ignore_lines,
                path=self.want.parents,
                diff_replace=replace
            )

            config_diff = response['config_diff']

            if config_diff:
                commands = config_diff.split('\n')

                if self.want.before:
                    commands[:0] = self.want.before

                if self.want.after:
                    commands.extend(self.want.after)

                result['commands'] = commands
                result['updates'] = commands

                if not self.module.check_mode:
                    self.load_config(commands)

                result['changed'] = True

        running_config = self.want.running_config
        startup_config = None

        if self.want.save_when == 'always':
            self.save_config(result)
        elif self.want.save_when == 'modified':
            output = self.execute_show_commands(['show running-config', 'show startup-config'])

            running_config = NetworkConfig(indent=1, contents=output[0], ignore_lines=self.want.diff_ignore_lines)
            startup_config = NetworkConfig(indent=1, contents=output[1], ignore_lines=self.want.diff_ignore_lines)

            if running_config.sha1 != startup_config.sha1:
                self.save_config(result)
        elif self.want.save_when == 'changed' and result['changed']:
            self.save_on_device()

        if self.module._diff:
            if not running_config:
                output = self.execute_show_commands('show running-config')
                contents = output[0]
            else:
                contents = running_config

            # recreate the object in order to process diff_ignore_lines
            running_config = NetworkConfig(indent=1, contents=contents, ignore_lines=self.want.diff_ignore_lines)

            if self.want.diff_against == 'running':
                if self.module.check_mode:
                    self.module.warn("unable to perform diff against running-config due to check mode")
                    contents = None
                else:
                    contents = config.config_text

            elif self.want.diff_against == 'startup':
                if not startup_config:
                    output = self.execute_show_commands('show startup-config')
                    contents = output[0]
                else:
                    contents = startup_config.config_text

            elif self.want.diff_against == 'intended':
                contents = self.want.intended_config

            if contents is not None:
                base_config = NetworkConfig(indent=1, contents=contents, ignore_lines=self.want.diff_ignore_lines)

                if running_config.sha1 != base_config.sha1:
                    if self.want.diff_against == 'intended':
                        before = running_config
                        after = base_config
                    elif self.want.diff_against in ('startup', 'running'):
                        before = base_config
                        after = running_config

                    result.update({
                        'changed': True,
                        'diff': {'before': str(before), 'after': str(after)}
                    })
        self.changes.update(result)
        return result['changed']

    def load_config(self, commands):
        content = StringIO("\n".join(commands))

        file = tempfile.NamedTemporaryFile()
        name = os.path.basename(file.name)

        self.upload_file_to_device(content, name)
        self.load_config_on_device(name)
        self.remove_uploaded_file_from_device(name)

    def remove_uploaded_file_from_device(self, name):
        filepath = '/var/config/rest/downloads/{0}'.format(name)
        params = {
            "command": "run",
            "utilCmdArgs": filepath
        }
        uri = "https://{0}:{1}/mgmt/tm/util/unix-rm".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def upload_file_to_device(self, content, name):
        url = 'https://{0}:{1}/mgmt/shared/file-transfer/uploads'.format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        try:
            upload_file(self.client, url, content, name)
        except F5ModuleError:
            raise F5ModuleError(
                "Failed to upload the file."
            )

    def load_config_on_device(self, name):
        filepath = '/var/config/rest/downloads/{0}'.format(name)
        command = 'imish -r {0} -f {1}'.format(self.want.route_domain, filepath)

        params = {
            "command": "run",
            "utilCmdArgs": '-c "{0}"'.format(command)
        }
        uri = "https://{0}:{1}/mgmt/tm/util/bash".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
            if 'commandResult' in response:
                if 'Dynamic routing is not enabled' in response['commandResult']:
                    raise F5ModuleError(response['commandResult'])
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def read_current_from_device(self):
        command = 'imish -r {0} -e \\\"show running-config\\\"'.format(self.want.route_domain)

        params = {
            "command": "run",
            "utilCmdArgs": '-c "{0}"'.format(command)
        }
        uri = "https://{0}:{1}/mgmt/tm/util/bash".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
            if 'commandResult' in response:
                if 'Dynamic routing is not enabled' in response['commandResult']:
                    raise F5ModuleError(response['commandResult'])
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return response['commandResult']

    def save_on_device(self):
        command = 'imish -e write'
        params = {
            "command": "run",
            "utilCmdArgs": '-c "{0}"'.format(command)
        }
        uri = "https://{0}:{1}/mgmt/tm/util/bash".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def get_diff(self, candidate=None, running=None, diff_match='line', diff_ignore_lines=None, path=None, diff_replace='line'):
        diff = {}

        # prepare candidate configuration
        candidate_obj = NetworkConfig(indent=1)
        candidate_obj.load(candidate)

        if running and diff_match != 'none' and diff_replace != 'config':
            # running configuration
            running_obj = NetworkConfig(indent=1, contents=running, ignore_lines=diff_ignore_lines)
            configdiffobjs = candidate_obj.difference(running_obj, path=path, match=diff_match, replace=diff_replace)
        else:
            configdiffobjs = candidate_obj.items

        diff['config_diff'] = dumps(configdiffobjs, 'commands') if configdiffobjs else ''
        return diff

    def get_running_config(self, config=None):
        contents = self.want.running_config
        if not contents:
            if config:
                contents = config
            else:
                contents = self.read_current_from_device()
        return contents

    def get_candidate(self):
        candidate = ''
        if self.want.src:
            candidate = self.want.src

        elif self.want.lines:
            candidate_obj = NetworkConfig(indent=1)
            parents = self.want.parents or list()
            candidate_obj.add(self.want.lines, parents=parents)
            candidate = dumps(candidate_obj, 'raw')
        return candidate

    def execute_show_commands(self, commands):
        body = []

        uri = "https://{0}:{1}/mgmt/tm/util/bash".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        for command in to_list(commands):
            command = 'imish -r {0} -e \\\"{1}\\\"'.format(self.want.route_domain, command)
            params = {
                "command": "run",
                "utilCmdArgs": '-c "{0}"'.format(command)
            }
            resp = self.client.api.post(uri, json=params)
            try:
                response = resp.json()
                if 'commandResult' in response:
                    if 'Dynamic routing is not enabled' in response['commandResult']:
                        raise F5ModuleError(response['commandResult'])
            except ValueError as ex:
                raise F5ModuleError(str(ex))
            if 'code' in response and response['code'] in [400, 403]:
                if 'message' in response:
                    raise F5ModuleError(response['message'])
                else:
                    raise F5ModuleError(resp.content)
            body.append(response['commandResult'])
        return body

    def save_config(self, result):
        result['changed'] = True
        if self.module.check_mode:
            self.module.warn(
                'Skipping command `copy running-config startup-config` '
                'due to check_mode.  Configuration not copied to '
                'non-volatile storage'
            )
            return
        self.save_on_device()


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        backup_spec = dict(
            filename=dict(),
            dir_path=dict(type='path')
        )
        argument_spec = dict(
            route_domain=dict(default=0),
            src=dict(type='path'),
            lines=dict(aliases=['commands'], type='list'),
            parents=dict(type='list'),

            before=dict(type='list'),
            after=dict(type='list'),

            match=dict(default='line', choices=['line', 'strict', 'exact', 'none']),
            replace=dict(default='line', choices=['line', 'block']),

            running_config=dict(aliases=['config']),
            intended_config=dict(),

            backup=dict(type='bool', default=False),
            backup_options=dict(type='dict', options=backup_spec),

            save_when=dict(choices=['always', 'never', 'modified', 'changed'], default='never'),

            diff_against=dict(choices=['running', 'startup', 'intended'], default='startup'),
            diff_ignore_lines=dict(type='list'),
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.mutually_exclusive = [
            ('lines', 'src'),
            ('parents', 'src'),
        ]
        self.required_if = [
            ('match', 'strict', ['lines']),
            ('match', 'exact', ['lines']),
            ('replace', 'block', ['lines']),
            ('diff_against', 'intended', ['intended_config'])
        ]
        self.add_file_common_args = True


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        mutually_exclusive=spec.mutually_exclusive,
        required_if=spec.required_if,
        add_file_common_args=spec.add_file_common_args,
    )

    client = F5RestClient(**module.params)

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
