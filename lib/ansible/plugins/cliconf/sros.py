# Copyright (c) 2019 - NOKIA Inc. All Rights Reserved.
# Please read the associated COPYRIGHTS file for more details.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
author: Nokia
cliconf: sros
short_description: Use sros cliconf to run command on Nokia SR OS devices
description:
  - This SROS plugin provides low level abstraction apis for sending and
    receiving CLI commands from Nokia SR OS network devices.
  - The plugin has been validated against SROS 19.
  - The plugin supports both classic CLI and model-driven CLI while it
    also allows to change between both modes in the same session interactively.
  - The plugin leverages MD CLI or configuration rollback in Classic CLI.
    Some base config must be in place to ensure functionality of this plugin.
  - For platforms that don't support md-cli or rollbacks neither, only
    cli_command can be used.
version_added: "2.9"
"""

import re
import json

from itertools import chain
from functools import wraps

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.common._collections_compat import Mapping
from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase, enable_mode


class Cliconf(CliconfBase):

    def get_device_operations(self):
        return {                                    # supported: ---------------
            'supports_commit': True,                # identify if commit is supported by device or not
            'supports_rollback': True,              # identify if rollback is supported or not
            'supports_defaults': True,              # identify if fetching running config with default is supported
            'supports_onbox_diff': True,            # identify if on box diff capability is supported or not
            'supports_config_replace': True,        # identify if running config replace with candidate config is supported
                                                    # unsupported: -------------
            'supports_admin': False,                # identify if admin configure mode is supported or not
            'supports_multiline_delimiter': False,  # identify if multiline demiliter is supported within config
            'supports_commit_label': False,         # identify if commit label is supported or not
            'supports_commit_comment': False,       # identify if adding comment to commit is supported of not
            'supports_generate_diff': False,        # not needed, as we support on box diff
            'supports_diff_replace': False,         # not needed, as we support on box diff
            'supports_diff_match': False,           # not needed, as we support on box diff
            'supports_diff_ignore_lines': False     # not needed, as we support on box diff
        }

    def get_sros_rpc(self):
        return [
            'get_config',          # Retrieves the specified configuration from the device
            'edit_config',         # Loads the specified commands into the remote device
            'get_capabilities',    # Retrieves device information and supported rpc methods
            'get',                 # Execute specified command on remote device
            'get_default_flag'     # CLI option to include defaults for config dumps
        ]

    def get_option_values(self):
        # format: json is supported from SROS19.10 onwards in MD MODE only
        return {
            'format': ['text', 'json'],
            'diff_match': [],
            'diff_replace': [],
            'output': ['text']
        }

    def get_device_info(self):
        device_info = {'network_os': 'sros'}

        reply = self.get('show system information')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'System Version\s+:\s+(.+)', data)
        if match:
            device_info['network_os_version'] = match.group(1)

        match = re.search(r'System Type\s+:\s+(.+)', data)
        if match:
            device_info['network_os_model'] = match.group(1)

        match = re.search(r'System Name\s+:\s+(.+)', data)
        if match:
            device_info['network_os_hostname'] = match.group(1)

        return device_info

    def get_capabilities(self):
        try:
            self.capabilities
        except NameError:
            self.capabilities = {}
            self.capabilities['device_operations'] = self.get_device_operations()
            self.capabilities['rpc'] = self.get_sros_rpc()
            self.capabilities['device_info'] = self.get_device_info()
            self.capabilities['network_api'] = 'cliconf'
            self.capabilities.update(self.get_option_values())

        return json.dumps(self.capabilities)

    def get_default_flag(self):
        return ['detail']

    def is_config_mode(self):
        """
        After a MD-CLI user has entered the edit-config command, the CLI
        session is in configuration mode. This is indicated by changing
        the CLI prompt as following:

        (ex)[...] - exclusive mode (locked) for candidate configuration
        (gl)[...] - global (shared) mode for candidate configuration
        (pr)[...] - private mode for candidate configuration
        (ro)[...] - read-only mode

        Ansible does not expose different edit-config modes, while this
        plugin is using private mode to avoid interference with concurrent
        CLI or NETCONF sessions.

        Note, that is Ansible module will use "edit-config private" and
        "quit-config" to enter and leave configuration mode. The
        alternative of using "configure private" is not supported.

        :return: True if session is running in configuration mode
        """

        return self._connection.get_prompt().strip().startswith('(')

    def is_classic_cli(self):
        """
        Determines if the session is running in Classic CLI or MD-CLI.
        Classic CLI uses a single line prompt while MD-CLI uses a multi
        line prompt. Setting is not static as it is possible to toggle
        between CLI engines:
          //             - toggle between modes
          /!md-cli       - set session to md-cli
          /!classic-cli  - set session to classic-cli

        It's also possible to execute single commands of the other
        engine by prepending the command with '//'.

        For integration purposes keep into consideration that MD mode
        and MD CLI are disabled by default. Please contact your Nokia
        SE/CE team to learn, if MD mode is supported on the platforms
        and releases used.

        :return: True if session is in classic CLI
        """

        return '\n' not in self._connection.get_prompt().strip()

    def get_config(self, source='running', format='text', flags=None):
        if self.is_classic_cli():
            # In classic CLI we are using the 'admin display config' command.
            # Reason is, that in classic CLI 'info' can not be used in context
            # of 'configure' but just for sub-contexts such as services.

            if source is not 'running':
                raise ValueError("fetching configuration from %s is not supported" % source)

            if format is not 'text':
                raise ValueError("'format' value %s is invalid. Only format supported is 'text'" % format)

            cmd = 'admin display-config %s' % ' '.join(flags)
            self.send_command('exit all')
            response = self.send_command(cmd.strip())
            pos1 = response.find('exit all')
            pos2 = response.rfind('exit all') + 8
            response = response[pos1:pos2]
        else:
            if source not in ('startup', 'running', 'candidate'):
                raise ValueError("fetching configuration from %s is not supported" % source)

            if format not in self.get_option_values()['format']:
                raise ValueError("'format' value %s is invalid. Valid values are %s" % (format, ','.join(self.get_option_values()['format'])))

            if format is 'text':
                cmd = 'info %s %s' % (source, ' '.join(flags))
            else:
                cmd = 'info %s %s %s' % (source, format, ' '.join(flags))

            self.send_command('exit all')
            if self.is_config_mode():
                # This Ansible module always quits config mode straight after
                # the CLI operation is done. In that sense querying candidate
                # does not make much sense, while we would always need to
                # change between configuration mode and operational mode.

                response = self.send_command(cmd.strip())
            else:
                # If this is a MD CLI session, we would always go here. We are
                # not using the 'admin show configuration' command, as 'info'
                # provides additional options such as 'info detail' to include
                # default values.

                if source is 'startup':
                    self.send_command('edit-config private')
                    self.send_command('configure')
                    self.send_command('rollback startup')
                    self.send_command('exit all')
                    response = self.send_command(cmd.strip())
                    self.send_command('discard')
                else:
                    self.send_command('edit-config read-only')
                    response = self.send_command(cmd.strip())
                self.send_command('quit-config')

        return response

    def edit_config(self, candidate=None, commit=True, replace=None, comment=None):
        operations = self.get_device_operations()
        self.check_edit_config_capability(operations, candidate, commit, replace, comment)

        if self.is_classic_cli():
            # In the case of classic CLI we are relying on the built-in rollback feature.
            # For that reason it is required that the rollback location is properly
            # configured. For example:
            #     A:Antwerp# file md cf3:/rollbacks
            #     *A:Antwerp# configure system rollback rollback-location cf3:/rollbacks/config
            #     INFO: CLI No checkpoints currently exist at the rollback location.
            #     *A:Antwerp# admin rollback save
            #     Saving rollback configuration to cf3:/rollbacks/config.rb... OK
            #     *A:Antwerp#
            # After every successful configuration change one need to make sure, that a
            # new checkpoint is created. Functionality is needed to rollback on failure
            # and to show differences.
            #
            # IMPORTANT RESTRICTIONS:
            #  (1) Some platforms might not support checkpoint/rollback
            #  (2) Changes are always written to running (implies commit=True)
            #  (3) Operation replace is currently not supported

            # NOTE: REMOVE THE FOLLOWING CODE, TO FAIL THE USE of commit=false ON SROS NODES RUNNING CLASSIC CLI
            #       MIGHT BE REQUIRED TO AVOID TEMPORARY ACTIVATION OF NEW CONFIGURATION IN CHECK_MODE

            # if not commit:
            #     raise ValueError("edit_config dryrun/preview using commit=False is currently not supported in Classic CLI")

            if replace:
                raise ValueError("edit_config replace operation is currently not supported in Classic CLI")

        requests = []
        responses = []
        self.send_command('exit all')

        if not self.is_classic_cli():
            if not self.is_config_mode():
                self.send_command('edit-config private')
            if replace and not candidate:
                cmd = 'configure'
                requests.append(cmd)
                responses.append(self.send_command(cmd))
                cmd = 'load full-replace {0}'.format(replace)
                requests.append(cmd)
                responses.append(self.send_command(cmd))
            elif replace:
                cmd = 'delete configure'
                requests.append(cmd)
                responses.append(self.send_command(cmd))

        try:
            for cmd in to_list(candidate):
                if isinstance(cmd, Mapping):
                    requests.append(cmd['command'])
                    responses.append(self.send_command(**cmd))
                else:
                    requests.append(cmd)
                    responses.append(self.send_command(cmd))

        except AnsibleConnectionFailure as exc:
            self.send_command('exit all')
            if self.is_classic_cli():
                self.send_command('admin rollback revert latest-rb')
            else:
                self.send_command('discard')
                self.send_command('quit-config')
            raise

        self.send_command('exit all')
        if self.is_classic_cli():
            rawdiffs = self.send_command('admin rollback compare')
            match = re.search(br'\r?\n-+\r?\n(.*)\r?\n-+\r?\n', rawdiffs, re.DOTALL)
            if match:
                diffs = match.group(1)
                if not commit:
                    # Special hack! We load the config to running and rollback
                    # to just figure out the delta. this might be risky in
                    # check-mode, because it causes the changes contained to
                    # become temporary active.

                    self.send_command('admin rollback revert latest-rb')

                self.send_command('admin rollback save')
            else:
                diffs = None
        else:
            diffs = self.send_command('compare').strip()
            if diffs:
                if commit:
                    self.send_command('commit')
                else:
                    self.send_command('validate')
                    self.send_command('discard')
            self.send_command('quit-config')

        if diffs:
            return {'request': requests, 'response': responses, 'diff': diffs}
        else:
            return {'request': requests, 'response': responses}

    def get(self, command, prompt=None, answer=None, sendonly=False, output=None, newline=True, check_all=False):
        if output:
            raise ValueError("'output' value %s is not supported for get" % output)
        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, newline=newline, check_all=check_all)

    def rollback(self, rollback_id, commit=True):
        self.send_command('exit all')

        if self.is_classic_cli():
            if str(rollback_id) is '0':
                rollback_id = 'latest-rb'
            rawdiffs = self.send_command('admin rollback compare {0} to active-cfg'.format(rollback_id))
            match = re.search(br'\r?\n-+\r?\n(.*)\r?\n-+\r?\n', rawdiffs, re.DOTALL)
            if match:
                if commit:
                    # After executing the rollback another checkpoint is generated
                    # This is required, to align running and latest-rb for follow-up requests
                    self.send_command('admin rollback revert {0}'.format(rollback_id))
                    self.send_command('admin rollback save')
                return {'diff': match.group(1)}
            return {}

        self.send_command('exit all')
        if not self.is_config_mode():
            self.send_command('edit-config private')
        self.send_command('configure')
        self.send_command('rollback {0}'.format(rollback_id))
        self.send_command('exit all')
        diffs = self.send_command('compare')
        if diffs.strip():
            if commit:
                self.send_command('commit')
            else:
                self.send_command('discard')

        self.send_command('quit-config')

        if diffs.strip():
            return {'diff': diffs.strip()}
        else:
            return {}
