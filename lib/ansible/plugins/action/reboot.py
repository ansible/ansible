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
from ansible.module_utils.common.validation import check_type_list, check_type_str
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()


class TimedOutException(Exception):
    pass


class ActionModule(ActionBase):
    TRANSFERS_FILES = False
    _VALID_ARGS = frozenset((
        'boot_time_command',
        'connect_timeout',
        'msg',
        'post_reboot_delay',
        'pre_reboot_delay',
        'reboot_command',
        'reboot_timeout',
        'search_paths',
        'test_command',
    ))

    DEFAULT_REBOOT_TIMEOUT = 600
    DEFAULT_CONNECT_TIMEOUT = None
    DEFAULT_PRE_REBOOT_DELAY = 0
    DEFAULT_POST_REBOOT_DELAY = 0
    DEFAULT_TEST_COMMAND = 'whoami'
    DEFAULT_BOOT_TIME_COMMAND = 'cat /proc/sys/kernel/random/boot_id'
    DEFAULT_REBOOT_MESSAGE = 'Reboot initiated by Ansible'
    DEFAULT_SHUTDOWN_COMMAND = 'shutdown'
    DEFAULT_SHUTDOWN_COMMAND_ARGS = '-r {delay_min} "{message}"'
    DEFAULT_SUDOABLE = True

    DEPRECATED_ARGS = {}  # type: dict[str, str]

    BOOT_TIME_COMMANDS = {
        'freebsd': '/sbin/sysctl kern.boottime',
        'openbsd': '/sbin/sysctl kern.boottime',
        'macosx': 'who -b',
        'solaris': 'who -b',
        'sunos': 'who -b',
        'vmkernel': 'grep booted /var/log/vmksummary.log | tail -n 1',
        'aix': 'who -b',
    }

    SHUTDOWN_COMMANDS = {
        'alpine': 'reboot',
        'vmkernel': 'reboot',
    }

    SHUTDOWN_COMMAND_ARGS = {
        'alpine': '',
        'void': '-r +{delay_min} "{message}"',
        'freebsd': '-r +{delay_sec}s "{message}"',
        'linux': DEFAULT_SHUTDOWN_COMMAND_ARGS,
        'macosx': '-r +{delay_min} "{message}"',
        'openbsd': '-r +{delay_min} "{message}"',
        'solaris': '-y -g {delay_sec} -i 6 "{message}"',
        'sunos': '-y -g {delay_sec} -i 6 "{message}"',
        'vmkernel': '-d {delay_sec}',
        'aix': '-Fr',
    }

    TEST_COMMANDS = {
        'solaris': 'who',
        'vmkernel': 'who',
    }

    def __init__(self, *args, **kwargs):
        super(ActionModule, self).__init__(*args, **kwargs)

    @property
    def pre_reboot_delay(self):
        return self._check_delay('pre_reboot_delay', self.DEFAULT_PRE_REBOOT_DELAY)

    @property
    def post_reboot_delay(self):
        return self._check_delay('post_reboot_delay', self.DEFAULT_POST_REBOOT_DELAY)

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
        reboot_command = self._task.args.get('reboot_command')
        if reboot_command is not None:
            try:
                reboot_command = check_type_str(reboot_command, allow_conversion=False)
            except TypeError as e:
                raise AnsibleError("Invalid value given for 'reboot_command': %s." % to_native(e))

            # No args were provided
            try:
                return reboot_command.split(' ', 1)[1]
            except IndexError:
                return ''
        else:
            args = self._get_value_from_facts('SHUTDOWN_COMMAND_ARGS', distribution, 'DEFAULT_SHUTDOWN_COMMAND_ARGS')

            # Convert seconds to minutes. If less that 60, set it to 0.
            delay_min = self.pre_reboot_delay // 60
            reboot_message = self._task.args.get('msg', self.DEFAULT_REBOOT_MESSAGE)
            return args.format(delay_sec=self.pre_reboot_delay, delay_min=delay_min, message=reboot_message)

    def get_distribution(self, task_vars):
        # FIXME: only execute the module if we don't already have the facts we need
        distribution = {}
        display.debug(f'{self._task.action}: running setup module to get distribution')
        module_output = self._execute_module(
            task_vars=task_vars,
            module_name='ansible.legacy.setup',
            module_args={'gather_subset': 'min'})
        try:
            if module_output.get('failed', False):
                raise AnsibleError(f'Failed to determine system distribution. {to_native(module_output['module_stdout']).strip()}, {to_native(module_output['module_stderr']).strip()}')
            distribution['name'] = module_output['ansible_facts']['ansible_distribution'].lower()
            distribution['version'] = to_text(module_output['ansible_facts']['ansible_distribution_version'].split('.')[0])
            distribution['family'] = to_text(module_output['ansible_facts']['ansible_os_family'].lower())
            display.debug(f"{self._task.action}: distribution: {distribution}")
            return distribution
        except KeyError as ke:
            raise AnsibleError(f'Failed to get distribution information. Missing "{ke.args[0]}" in output.')

    def get_shutdown_command(self, task_vars, distribution):
        reboot_command = self._task.args.get('reboot_command')
        if reboot_command is not None:
            try:
                reboot_command = check_type_str(reboot_command, allow_conversion=False)
            except TypeError as e:
                raise AnsibleError("Invalid value given for 'reboot_command': %s." % to_native(e))
            shutdown_bin = reboot_command.split(' ', 1)[0]
        else:
            shutdown_bin = self._get_value_from_facts('SHUTDOWN_COMMANDS', distribution, 'DEFAULT_SHUTDOWN_COMMAND')

        if shutdown_bin[0] == '/':
            return shutdown_bin
        else:
            default_search_paths = ['/sbin', '/bin', '/usr/sbin', '/usr/bin', '/usr/local/sbin']
            search_paths = self._task.args.get('search_paths', default_search_paths)

            try:
                # Convert bare strings to a list
                search_paths = check_type_list(search_paths)
            except TypeError:
                err_msg = "'search_paths' must be a string or flat list of strings, got {0}"
                raise AnsibleError(err_msg.format(search_paths))

            display.debug(f'{self._task.action}: running find module looking in {search_paths} to get path for "{shutdown_bin}"')

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
                raise AnsibleError(f'Unable to find command "{shutdown_bin}" in search paths: {search_paths}')
            return full_path[0]

    def deprecated_args(self):
        for arg, version in self.DEPRECATED_ARGS.items():
            if self._task.args.get(arg) is not None:
                display.warning(f"Since Ansible {version}, {arg} is no longer a valid option for {self._task.action}")

    def get_system_boot_time(self, distribution):
        boot_time_command = self._get_value_from_facts('BOOT_TIME_COMMANDS', distribution, 'DEFAULT_BOOT_TIME_COMMAND')
        if self._task.args.get('boot_time_command'):
            boot_time_command = self._task.args.get('boot_time_command')

            try:
                check_type_str(boot_time_command, allow_conversion=False)
            except TypeError as e:
                raise AnsibleError("Invalid value given for 'boot_time_command': %s." % to_native(e))

        display.debug(f"{self._task.action}: getting boot time with command: '{boot_time_command}'")
        command_result = self._low_level_execute_command(boot_time_command, sudoable=self.DEFAULT_SUDOABLE)

        if command_result['rc'] != 0:
            stdout = command_result['stdout']
            stderr = command_result['stderr']
            raise AnsibleError(f"{self._task.action}: failed to get host boot time info, rc: {command_result['rc']}, stdout: {to_native(stdout)}, stderr: {to_native(stderr)}")
        display.debug(f"{self._task.action}: last boot time: {command_result['stdout'].strip()}")
        return command_result['stdout'].strip()

    def check_boot_time(self, distribution, previous_boot_time):
        display.vvv(f"{self._task.action}: attempting to get system boot time")
        connect_timeout = self._task.args.get('connect_timeout', self._task.args.get('connect_timeout_sec', self.DEFAULT_CONNECT_TIMEOUT))

        # override connection timeout from defaults to custom value
        if connect_timeout:
            try:
                display.debug(f"{self._task.action}: setting connect_timeout to {connect_timeout}")
                self._connection.set_option("connection_timeout", connect_timeout)
                self._connection.reset()
            except AttributeError:
                display.warning("Connection plugin does not allow the connection timeout to be overridden")

        # try and get boot time
        try:
            current_boot_time = self.get_system_boot_time(distribution)
        except Exception as e:
            raise e

        # FreeBSD returns an empty string immediately before reboot so adding a length
        # check to prevent prematurely assuming system has rebooted
        if len(current_boot_time) == 0 or current_boot_time == previous_boot_time:
            raise ValueError("boot time has not changed")

    def run_test_command(self, distribution, **kwargs):
        test_command = self._task.args.get('test_command', self._get_value_from_facts('TEST_COMMANDS', distribution, 'DEFAULT_TEST_COMMAND'))
        display.vvv(f"{self._task.action}: attempting post-reboot test command")
        display.debug(f"{self._task.action}: attempting post-reboot test command '{test_command}'")
        try:
            command_result = self._low_level_execute_command(test_command, sudoable=self.DEFAULT_SUDOABLE)
        except Exception:
            # may need to reset the connection in case another reboot occurred
            # which has invalidated our connection
            try:
                self._connection.reset()
            except AttributeError:
                pass
            raise

        if command_result['rc'] != 0:
            msg = f'Test command failed: {to_native(command_result['stderr'])} {to_native(command_result['stdout'])}'
            raise RuntimeError(msg)

        display.vvv(f"{self._task.action}: system successfully rebooted")

    def do_until_success_or_timeout(self, action, reboot_timeout, action_desc, distribution, action_kwargs=None):
        max_end_time = datetime.utcnow() + timedelta(seconds=reboot_timeout)
        if action_kwargs is None:
            action_kwargs = {}

        fail_count = 0
        max_fail_sleep = 12

        while datetime.utcnow() < max_end_time:
            try:
                action(distribution=distribution, **action_kwargs)
                if action_desc:
                    display.debug(f'{self._task.action}: {action_desc} success')
                return
            except Exception as e:
                if isinstance(e, AnsibleConnectionFailure):
                    try:
                        self._connection.reset()
                    except AnsibleConnectionFailure:
                        pass
                # Use exponential backoff with a max timout, plus a little bit of randomness
                random_int = random.randint(0, 1000) / 1000
                fail_sleep = 2 ** fail_count + random_int
                if fail_sleep > max_fail_sleep:

                    fail_sleep = max_fail_sleep + random_int
                if action_desc:
                    try:
                        error = to_text(e).splitlines()[-1]
                    except IndexError as e:
                        error = to_text(e)
                    display.debug(f"{self._task.action}: {action_desc} fail '{error}', retrying in {fail_sleep:.4} seconds...")
                fail_count += 1
                time.sleep(fail_sleep)

        raise TimedOutException(f'Timed out waiting for {action_desc} (timeout={reboot_timeout})')

    def perform_reboot(self, task_vars, distribution):
        result = {}
        reboot_result = {}
        shutdown_command = self.get_shutdown_command(task_vars, distribution)
        shutdown_command_args = self.get_shutdown_command_args(distribution)
        reboot_command = f'{shutdown_command} {shutdown_command_args}'

        try:
            display.vvv(f"{self._task.action}: rebooting server...")
            display.debug(f"{self._task.action}: rebooting server with command '{reboot_command}'")
            reboot_result = self._low_level_execute_command(reboot_command, sudoable=self.DEFAULT_SUDOABLE)
        except AnsibleConnectionFailure as e:
            # If the connection is closed too quickly due to the system being shutdown, carry on
            display.debug(f'{self._task.action}: AnsibleConnectionFailure caught and handled: {to_text(e)}')
            reboot_result['rc'] = 0

        result['start'] = datetime.utcnow()

        if reboot_result['rc'] != 0:
            result['failed'] = True
            result['rebooted'] = False
            result['msg'] = f"Reboot command failed. Error was: '{to_native(reboot_result['stdout'].strip())}, {to_native(reboot_result['stderr'].strip())}'"
            return result

        result['failed'] = False
        return result

    def validate_reboot(self, distribution, original_connection_timeout=None, action_kwargs=None):
        display.vvv(f'{self._task.action}: validating reboot')
        result = {}

        try:
            # keep on checking system boot_time with short connection responses
            reboot_timeout = int(self._task.args.get('reboot_timeout', self._task.args.get('reboot_timeout_sec', self.DEFAULT_REBOOT_TIMEOUT)))

            self.do_until_success_or_timeout(
                action=self.check_boot_time,
                action_desc="last boot time check",
                reboot_timeout=reboot_timeout,
                distribution=distribution,
                action_kwargs=action_kwargs)

            # Get the connect_timeout set on the connection to compare to the original
            try:
                connect_timeout = self._connection.get_option('connection_timeout')
            except KeyError:
                pass
            else:
                if original_connection_timeout != connect_timeout:
                    try:
                        display.debug(f"{self._task.action}: setting connect_timeout back to original value of {original_connection_timeout}")
                        self._connection.set_option("connection_timeout", original_connection_timeout)
                        self._connection.reset()
                    except (AnsibleError, AttributeError) as e:
                        # reset the connection to clear the custom connection timeout
                        display.debug(f"{self._task.action}: failed to reset connection_timeout back to default: {to_text(e)}".)

            # finally run test command to ensure everything is working
            # FUTURE: add a stability check (system must remain up for N seconds) to deal with self-multi-reboot updates
            self.do_until_success_or_timeout(
                action=self.run_test_command,
                action_desc="post-reboot test command",
                reboot_timeout=reboot_timeout,
                distribution=distribution,
                action_kwargs=action_kwargs)

            result['rebooted'] = True
            result['changed'] = True

        except TimedOutException as toex:
            result['failed'] = True
            result['rebooted'] = True
            result['msg'] = to_text(toex)
            return result

        return result

    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = True
        self._supports_async = True

        # If running with local connection, fail so we don't reboot ourself
        if self._connection.transport == 'local':
            msg = f'Running {self._task.action} with local connection would reboot the control node.'
            return {'changed': False, 'elapsed': 0, 'rebooted': False, 'failed': True, 'msg': msg}

        if self._play_context.check_mode:
            return {'changed': True, 'elapsed': 0, 'rebooted': True}

        if task_vars is None:
            task_vars = {}

        self.deprecated_args()

        result = super(ActionModule, self).run(tmp, task_vars)

        if result.get('skipped', False) or result.get('failed', False):
            return result

        distribution = self.get_distribution(task_vars)

        # Get current boot time
        try:
            previous_boot_time = self.get_system_boot_time(distribution)
        except Exception as e:
            result['failed'] = True
            result['reboot'] = False
            result['msg'] = to_text(e)
            return result

        # Get the original connection_timeout option var so it can be reset after
        original_connection_timeout = None
        try:
            original_connection_timeout = self._connection.get_option('connection_timeout')
            display.debug(f"{self._task.action}: saving original connect_timeout of {original_connection_timeout}".format(action=self._task.action, timeout=))
        except KeyError:
            display.debug(f"{self._task.action}: connect_timeout connection option has not been set".format(action=self._task.action))
        # Initiate reboot
        reboot_result = self.perform_reboot(task_vars, distribution)

        if reboot_result['failed']:
            result = reboot_result
            elapsed = datetime.utcnow() - reboot_result['start']
            result['elapsed'] = elapsed.seconds
            return result

        if self.post_reboot_delay != 0:
            display.debug(f"{self._task.action}: waiting an additional {self.post_reboot_delay} seconds")
            display.vvv(f"{self._task.action}: waiting an additional {self.post_reboot_delay} seconds")
            time.sleep(self.post_reboot_delay)

        # Make sure reboot was successful
        result = self.validate_reboot(distribution, original_connection_timeout, action_kwargs={'previous_boot_time': previous_boot_time})

        elapsed = datetime.utcnow() - reboot_result['start']
        result['elapsed'] = elapsed.seconds

        return result
