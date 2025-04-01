# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
    name: runas
    short_description: Run As user
    description:
        - This become plugin allows your remote/login user to execute commands as another user via the windows runas facility.
    author: ansible (@core)
    version_added: "2.8"
    options:
        become_user:
            description: User you 'become' to execute the task
            ini:
              - section: privilege_escalation
                key: become_user
              - section: runas_become_plugin
                key: user
            vars:
              - name: ansible_become_user
              - name: ansible_runas_user
            env:
              - name: ANSIBLE_BECOME_USER
              - name: ANSIBLE_RUNAS_USER
            keyword:
              - name: become_user
            required: True
        become_flags:
            description: Options to pass to runas, a space delimited list of k=v pairs
            default: ''
            ini:
              - section: privilege_escalation
                key: become_flags
              - section: runas_become_plugin
                key: flags
            vars:
              - name: ansible_become_flags
              - name: ansible_runas_flags
            env:
              - name: ANSIBLE_BECOME_FLAGS
              - name: ANSIBLE_RUNAS_FLAGS
            keyword:
              - name: become_flags
        become_pass:
            description: password
            ini:
              - section: runas_become_plugin
                key: password
            vars:
              - name: ansible_become_password
              - name: ansible_become_pass
              - name: ansible_runas_pass
            env:
              - name: ANSIBLE_BECOME_PASS
              - name: ANSIBLE_RUNAS_PASS
    notes:
        - runas is really implemented in the powershell module handler and as such can only be used with winrm connections.
        - This plugin ignores the 'become_exe' setting as it uses an API and not an executable.
        - The Secondary Logon service (seclogon) must be running to use runas
"""

from ansible.errors import AnsibleError
from ansible.parsing.splitter import split_args
from ansible.plugins.become import BecomeBase


class BecomeModule(BecomeBase):

    name = 'runas'

    def build_become_command(self, cmd, shell):
        # this is a noop, the 'real' runas is implemented
        # inside the windows powershell execution subsystem
        return cmd

    def _build_powershell_wrapper_action(self) -> tuple[str, dict[str, object], dict[str, object]]:
        # See ansible.executor.powershell.become_wrapper.ps1 for the
        # parameter names
        params = {
            'BecomeUser': self.get_option('become_user'),
        }
        secure_params = {}

        password = self.get_option('become_pass')
        if password:
            secure_params['BecomePassword'] = password

        flags = self.get_option('become_flags')
        if flags:
            split_flags = split_args(flags)
            for flag in split_flags:
                if '=' not in flag:
                    raise ValueError(f"become_flags entry '{flag}' is in an invalid format, must be a key=value pair")

                k, v = flag.split('=', 1)

                param_name, param_value = self._parse_flag(k, v)
                params[param_name] = param_value

        return 'become_wrapper.ps1', params, secure_params

    def _parse_flag(self, name: str, value: str) -> tuple[str, str]:
        logon_types = {
            'interactive': 'Interactive',
            'network': 'Network',
            'batch': 'Batch',
            'service': 'Service',
            'unlock': 'Unlock',
            'network_cleartext': 'NetworkCleartext',
            'new_credentials': 'NewCredentials',
        }
        logon_flags = {
            'none': 'None',
            'with_profile': 'WithProfile',
            'netcredentials_only': 'NetCredentialsOnly',
        }

        match name.lower():
            case 'logon_type':
                param_name = 'LogonType'
                if param_value := logon_types.get(value.lower(), None):
                    return param_name, param_value
                else:
                    raise AnsibleError(f"become_flags logon_type value '{value}' is not valid, valid values are: {', '.join(logon_types.keys())}")

            case 'logon_flags':
                param_name = 'LogonFlags'
                flags = value.split(',')

                param_values: list[str] = []
                for flag in flags:
                    if not flag:
                        continue

                    if flag_value := logon_flags.get(flag.lower(), None):
                        param_values.append(flag_value)
                    else:
                        raise AnsibleError(f"become_flags logon_flags value '{flag}' is not valid, valid values are: {', '.join(logon_flags.keys())}")

                return param_name, ", ".join(param_values)

            case _:
                raise AnsibleError(f"become_flags key '{name}' is not a valid runas flag, must be 'logon_type' or 'logon_flags'")
