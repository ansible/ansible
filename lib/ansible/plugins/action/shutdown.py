# Copyright: (c) 2016-2018, Matt Davis <mdavis@ansible.com>
# Copyright: (c) 2018, Sam Doran <sdoran@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import random
import time

from datetime import datetime, timedelta

from ansible.errors import AnsibleError, AnsibleConnectionFailure
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.common.collections import is_string
from ansible.module_utils.common.validation import check_type_str
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()


class TimedOutException(Exception):
    pass


class ActionModule(ActionBase):
    TRANSFERS_FILES = False
    _VALID_ARGS = frozenset((
        'connect_timeout',
        'msg',
        'pre_shutdown_delay',
        'search_paths'
    ))

    DEFAULT_CONNECT_TIMEOUT = None
    DEFAULT_PRE_SHUTDOWN_DELAY = 0
    DEFAULT_SHUTDOWN_MESSAGE = 'Shut down initiated by Ansible'
    DEFAULT_SHUTDOWN_COMMAND = 'shutdown'
    DEFAULT_SHUTDOWN_COMMAND_ARGS = '-h {delay_min} "{message}"'
    DEFAULT_SUDOABLE = True

    DEPRECATED_ARGS = {}

    SHUTDOWN_COMMANDS = {
        'alpine': 'poweroff',
        'vmkernel': 'halt',
    }

    SHUTDOWN_COMMAND_ARGS = {
        'alpine': '',
        'void': '-h +{delay_min} "{message}"',
        'freebsd': '-h +{delay_sec}s "{message}"',
        'linux': DEFAULT_SHUTDOWN_COMMAND_ARGS,
        'macosx': '-h +{delay_min} "{message}"',
        'openbsd': '-h +{delay_min} "{message}"',
        'solaris': '-y -g {delay_sec} -i 5 "{message}"',
        'sunos': '-y -g {delay_sec} -i 5 "{message}"',
        'vmkernel': '-d {delay_sec}',
        'aix': '-Fh',
    }

    def __init__(self, *args, **kwargs):
        super(ActionModule, self).__init__(*args, **kwargs)

    @property
    def pre_shutdown_delay(self):
        return self._check_delay('pre_shutdown_delay', self.DEFAULT_PRE_SHUTDOWN_DELAY)

    def _check_delay(self, key, default):
        """Ensure that the value is positive or zero"""
        value = int(self._task.args.get(key, self._task.args.get(key + '_sec', default)))
        if value < 0:
            value = 0
        return value

    def _get_value_from_facts(self, variable_name, distribution, default_value):
        """Get dist+version specific args first, then distribution, then family, lastly use default"""
        attr = getattr(self, variable_name)
        value = attr.get(
            distribution['name'] + distribution['version'],
            attr.get(
                distribution['name'],
                attr.get(
                    distribution['family'],
                    getattr(self, default_value))))
        return value

    def get_shutdown_command_args(self, distribution):
        args = self._get_value_from_facts('SHUTDOWN_COMMAND_ARGS', distribution, 'DEFAULT_SHUTDOWN_COMMAND_ARGS')
        # Convert seconds to minutes. If less that 60, set it to 0.
        delay_min = self.pre_shutdown_delay // 60
        shutdown_message = self._task.args.get('msg', self.DEFAULT_SHUTDOWN_MESSAGE)
        return args.format(delay_sec=self.pre_shutdown_delay, delay_min=delay_min, message=shutdown_message)

    def get_distribution(self, task_vars):
        # FIXME: only execute the module if we don't already have the facts we need
        distribution = {}
        display.debug('{action}: running setup module to get distribution'.format(action=self._task.action))
        module_output = self._execute_module(
            task_vars=task_vars,
            module_name='ansible.legacy.setup',
            module_args={'gather_subset': 'min'})
        try:
            if module_output.get('failed', False):
                raise AnsibleError('Failed to determine system distribution. {0}, {1}'.format(
                    to_native(module_output['module_stdout']).strip(),
                    to_native(module_output['module_stderr']).strip()))
            distribution['name'] = module_output['ansible_facts']['ansible_distribution'].lower()
            distribution['version'] = to_text(module_output['ansible_facts']['ansible_distribution_version'].split('.')[0])
            distribution['family'] = to_text(module_output['ansible_facts']['ansible_os_family'].lower())
            display.debug("{action}: distribution: {dist}".format(action=self._task.action, dist=distribution))
            return distribution
        except KeyError as ke:
            raise AnsibleError('Failed to get distribution information. Missing "{0}" in output.'.format(ke.args[0]))

    def get_shutdown_command(self, task_vars, distribution):
        shutdown_bin = self._get_value_from_facts('SHUTDOWN_COMMANDS', distribution, 'DEFAULT_SHUTDOWN_COMMAND')
        default_search_paths = ['/sbin', '/usr/sbin', '/usr/local/sbin']
        search_paths = self._task.args.get('search_paths', default_search_paths)

        # FIXME: switch all this to user arg spec validation methods when they are available
        # Convert bare strings to a list
        if is_string(search_paths):
            search_paths = [search_paths]

        # Error if we didn't get a list
        err_msg = "'search_paths' must be a string or flat list of strings, got {0}"
        try:
            incorrect_type = any(not is_string(x) for x in search_paths)
            if not isinstance(search_paths, list) or incorrect_type:
                raise TypeError
        except TypeError:
            raise AnsibleError(err_msg.format(search_paths))

        display.debug('{action}: running find module looking in {paths} to get path for "{command}"'.format(
            action=self._task.action,
            command=shutdown_bin,
            paths=search_paths))
        find_result = self._execute_module(
            task_vars=task_vars,
            # prevent collection search by calling with ansible.legacy (still allows library/ override of find)
            module_name='ansible.legacy.find',
            module_args={
                'paths': search_paths,
                'patterns': [shutdown_bin],
                'file_type': 'any'
            }
        )

        full_path = [x['path'] for x in find_result['files']]
        if not full_path:
            raise AnsibleError('Unable to find command "{0}" in search paths: {1}'.format(shutdown_bin, search_paths))
        self._shutdown_command = full_path[0]
        return self._shutdown_command

    def deprecated_args(self):
        for arg, version in self.DEPRECATED_ARGS.items():
            if self._task.args.get(arg) is not None:
                display.warning("Since Ansible {version}, {arg} is no longer a valid option for {action}".format(
                    version=version,
                    arg=arg,
                    action=self._task.action))

    def perform_shutdown(self, task_vars, distribution):
        result = {}
        shutdown_result = {}
        shutdown_command = self.get_shutdown_command(task_vars, distribution)
        shutdown_command_args = self.get_shutdown_command_args(distribution)
        shutdown_command_exec = '{0} {1}'.format(shutdown_command, shutdown_command_args)

        try:
            display.vvv("{action}: shutting down server...".format(action=self._task.action))
            display.debug("{action}: shutting down server with command '{command}'".format(action=self._task.action, command=shutdown_command_exec))
            shutdown_result = self._low_level_execute_command(shutdown_command_exec, sudoable=self.DEFAULT_SUDOABLE)
        except AnsibleConnectionFailure as e:
            # If the connection is closed too quickly due to the system being shutdown, carry on
            display.debug('{action}: AnsibleConnectionFailure caught and handled: {error}'.format(action=self._task.action, error=to_text(e)))
            shutdown_result['rc'] = 0

#        if shutdown_result['rc'] != 0:
#            result['failed'] = True
#            result['shutdown'] = False
#            result['msg'] = "Shutdown command failed. Error was {stdout}, {stderr}".format(
#                stdout=to_native(shutdown_result['stdout'].strip()),
#                stderr=to_native(shutdown_result['stderr'].strip()))
#            return result

        result['failed'] = False
        return result

    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = True
        self._supports_async = True

        # If running with local connection, fail so we don't shutdown ourself
        if self._connection.transport == 'local':
            msg = 'Running {0} with local connection would shutdown the control node.'.format(self._task.action)
            return {'changed': False, 'elapsed': 0, 'shutdown': False, 'failed': True, 'msg': msg}

        if self._play_context.check_mode:
            return {'changed': True, 'elapsed': 0, 'shutdown': True}

        if task_vars is None:
            task_vars = {}

        self.deprecated_args()

        result = super(ActionModule, self).run(tmp, task_vars)

        if result.get('skipped', False) or result.get('failed', False):
            return result

        distribution = self.get_distribution(task_vars)

        # Get the original connection_timeout option var so it can be reset after
        original_connection_timeout = None
        try:
            original_connection_timeout = self._connection.get_option('connection_timeout')
            display.debug("{action}: saving original connect_timeout of {timeout}".format(action=self._task.action, timeout=original_connection_timeout))
        except KeyError:
            display.debug("{action}: connect_timeout connection option has not been set".format(action=self._task.action))
        # Initiate shutdown
        shutdown_result = self.perform_shutdown(task_vars, distribution)

        if shutdown_result['failed']:
            result = shutdown_result
            return result

        result['shutdown'] = True
        result['changed'] = True

        return result
