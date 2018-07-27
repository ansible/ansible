#
# (c) 2017 Red Hat Inc.
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from abc import abstractmethod
from functools import wraps

from ansible.plugins import AnsiblePlugin
from ansible.errors import AnsibleError, AnsibleConnectionFailure
from ansible.module_utils._text import to_bytes, to_text


try:
    from scp import SCPClient
    HAS_SCP = True
except ImportError:
    HAS_SCP = False

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


def enable_mode(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        prompt = self._connection.get_prompt()
        if not to_text(prompt, errors='surrogate_or_strict').strip().endswith('#'):
            raise AnsibleError('operation requires privilege escalation')
        return func(self, *args, **kwargs)
    return wrapped


class CliconfBase(AnsiblePlugin):
    """
    A base class for implementing cli connections

    .. note:: String inputs to :meth:`send_command` will be cast to byte strings
         within this method and as such are not required to be made byte strings
         beforehand.  Please avoid using literal byte strings (``b'string'``) in
         :class:`CliConfBase` plugins as this can lead to unexpected errors when
         running on Python 3

    List of supported rpc's:
        :get_config: Retrieves the specified configuration from the device
        :edit_config: Loads the specified commands into the remote device
        :get: Execute specified command on remote device
        :get_capabilities: Retrieves device information and supported rpc methods
        :commit: Load configuration from candidate to running
        :discard_changes: Discard changes to candidate datastore

    Note: List of supported rpc's for remote device can be extracted from
          output of get_capabilities()

    :returns: Returns output received from remote device as byte string

            Usage:
            from ansible.module_utils.connection import Connection

            conn = Connection()
            conn.get('show lldp neighbors detail'')
            conn.get_config('running')
            conn.edit_config(['hostname test', 'netconf ssh'])
    """

    __rpc__ = ['get_config', 'edit_config', 'get_capabilities', 'get', 'enable_response_logging', 'disable_response_logging']

    def __init__(self, connection):
        super(CliconfBase, self).__init__()
        self._connection = connection
        self.history = list()
        self.response_logging = False

    def _alarm_handler(self, signum, frame):
        """Alarm handler raised in case of command timeout """
        display.display('closing shell due to command timeout (%s seconds).' % self._connection._play_context.timeout, log_only=True)
        self.close()

    def send_command(self, command=None, prompt=None, answer=None, sendonly=False, newline=True, prompt_retry_check=False):
        """Executes a command over the device connection

        This method will execute a command over the device connection and
        return the results to the caller.  This method will also perform
        logging of any commands based on the `nolog` argument.

        :param command: The command to send over the connection to the device
        :param prompt: A single regex pattern or a sequence of patterns to evaluate the expected prompt from the command
        :param answer: The answer to respond with if the prompt is matched.
        :param sendonly: Bool value that will send the command but not wait for a result.
        :param newline: Bool value that will append the newline character to the command
        :param prompt_retry_check: Bool value for trying to detect more prompts

        :returns: The output from the device after executing the command
        """
        kwargs = {
            'command': to_bytes(command),
            'sendonly': sendonly,
            'newline': newline,
            'prompt_retry_check': prompt_retry_check
        }

        if prompt is not None:
            if isinstance(prompt, list):
                kwargs['prompt'] = [to_bytes(p) for p in prompt]
            else:
                kwargs['prompt'] = to_bytes(prompt)
        if answer is not None:
            kwargs['answer'] = to_bytes(answer)

        resp = self._connection.send(**kwargs)

        if not self.response_logging:
            self.history.append(('*****', '*****'))
        else:
            self.history.append((kwargs['command'], resp))

        return resp

    def get_base_rpc(self):
        """Returns list of base rpc method supported by remote device"""
        return self.__rpc__

    def get_history(self):
        """ Returns the history file for all commands

        This will return a log of all the commands that have been sent to
        the device and all of the output received.  By default, all commands
        and output will be redacted unless explicitly configured otherwise.

        :return: An ordered list of command, output pairs
        """
        return self.history

    def reset_history(self):
        """ Resets the history of run commands
        :return: None
        """
        self.history = list()

    def enable_response_logging(self):
        """Enable logging command response"""
        self.response_logging = True

    def disable_response_logging(self):
        """Disable logging command response"""
        self.response_logging = False

    @abstractmethod
    def get_config(self, source='running', filter=None, format=None):
        """Retrieves the specified configuration from the device

        This method will retrieve the configuration specified by source and
        return it to the caller as a string.  Subsequent calls to this method
        will retrieve a new configuration from the device

        :param source: The configuration source to return from the device.
            This argument accepts either `running` or `startup` as valid values.

        :param filter: For devices that support configuration filtering, this
            keyword argument is used to filter the returned configuration.
            The use of this keyword argument is device dependent adn will be
            silently ignored on devices that do not support it.

        :param format: For devices that support fetching different configuration
            format, this keyword argument is used to specify the format in which
            configuration is to be retrieved.

        :return: The device configuration as specified by the source argument.
        """
        pass

    @abstractmethod
    def edit_config(self, candidate=None, commit=True, replace=None, diff=False, comment=None):
        """Loads the candidate configuration into the network device

        This method will load the specified candidate config into the device
        and merge with the current configuration unless replace is set to
        True.  If the device does not support config replace an errors
        is returned.

        :param candidate: The configuration to load into the device and merge
            with the current running configuration

        :param commit: Boolean value that indicates if the device candidate
            configuration should be  pushed in the running configuration or discarded.

        :param replace: If the value is True/False it indicates if running configuration should be completely
                        replace by candidate configuration. If can also take configuration file path as value,
                        the file in this case should be present on the remote host in the mentioned path as a
                        prerequisite.
        :param comment: Commit comment provided it is supported by remote host
        :return: Returns a json string with contains configuration applied on remote host, the returned
                 response on executing configuration commands and platform relevant data.
               {
                   "diff": "",
                   "response": []
               }

        """
        pass

    @abstractmethod
    def get(self, command=None, prompt=None, answer=None, sendonly=False, newline=True, output=None):
        """Execute specified command on remote device
        This method will retrieve the specified data and
        return it to the caller as a string.
        :param command: command in string format to be executed on remote device
        :param prompt: the expected prompt generated by executing command, this can
                       be a string or a list of strings
        :param answer: the string to respond to the prompt with
        :param sendonly: bool to disable waiting for response, default is false
        :param newline: bool to indicate if newline should be added at end of answer or not
        :param output: For devices that support fetching command output in different
            format, this keyword argument is used to specify the output in which
            response is to be retrieved.
        :return:
        """
        pass

    @abstractmethod
    def get_capabilities(self):
        """Returns the basic capabilities of the network device
        This method will provide some basic facts about the device and
        what capabilities it has to modify the configuration.  The minimum
        return from this method takes the following format.
        eg:
            {

                'rpc': [list of supported rpcs],
                'network_api': <str>,            # the name of the transport
                'device_info': {
                    'network_os': <str>,
                    'network_os_version': <str>,
                    'network_os_model': <str>,
                    'network_os_hostname': <str>,
                    'network_os_image': <str>,
                    'network_os_platform': <str>,
                },
                'device_operations': {
                    'supports_diff_replace': <bool>,       # identify if config should be merged or replaced is supported
                    'supports_commit': <bool>,             # identify if commit is supported by device or not
                    'supports_rollback': <bool>,           # identify if rollback is supported or not
                    'supports_defaults': <bool>,           # identify if fetching running config with default is supported
                    'supports_commit_comment': <bool>,     # identify if adding comment to commit is supported of not
                    'supports_onbox_diff: <bool>,          # identify if on box diff capability is supported or not
                    'supports_generate_diff: <bool>,       # identify if diff capability is supported within plugin
                    'supports_multiline_delimiter: <bool>, # identify if multiline demiliter is supported within config
                    'supports_diff_match: <bool>,           # identify if match is supported
                    'supports_diff_ignore_lines: <bool>,    # identify if ignore line in diff is supported
                    'supports_config_replace': <bool>,      # identify if running config replace with candidate config is supported
                }
                'format': [list of supported configuration format],
                'diff_match': [list of supported match values],
                'diff_replace': [list of supported replace values],
                'output': [list of supported command output format]
            }
        :return: capability as json string
        """
        pass

    def commit(self, comment=None):
        """Commit configuration changes

        This method will perform the commit operation on a previously loaded
        candidate configuration that was loaded using `edit_config()`.  If
        there is a candidate configuration, it will be committed to the
        active configuration.  If there is not a candidate configuration, this
        method should just silently return.

        :return: None
        """
        return self._connection.method_not_found("commit is not supported by network_os %s" % self._play_context.network_os)

    def discard_changes(self):
        """Discard candidate configuration

        This method will discard the current candidate configuration if one
        is present.  If there is no candidate configuration currently loaded,
        then this method should just silently return

        :returns: None
        """
        return self._connection.method_not_found("discard_changes is not supported by network_os %s" % self._play_context.network_os)

    def copy_file(self, source=None, destination=None, proto='scp', timeout=30):
        """Copies file over scp/sftp to remote device

        :param source: Source file path
        :param destination: Destination file path on remote device
        :param proto: Protocol to be used for file transfer,
                      supported protocol: scp and sftp
        :param timeout: Specifies the wait time to receive response from
                        remote host before triggering timeout exception
        :return: None
        """
        ssh = self._connection.paramiko_conn._connect_uncached()
        if proto == 'scp':
            if not HAS_SCP:
                raise AnsibleError("Required library scp is not installed.  Please install it using `pip install scp`")
            with SCPClient(ssh.get_transport(), socket_timeout=timeout) as scp:
                out = scp.put(source, destination)
        elif proto == 'sftp':
            with ssh.open_sftp() as sftp:
                sftp.put(source, destination)

    def get_file(self, source=None, destination=None, proto='scp', timeout=30):
        """Fetch file over scp/sftp from remote device
        :param source: Source file path
        :param destination: Destination file path
        :param proto: Protocol to be used for file transfer,
                      supported protocol: scp and sftp
        :param timeout: Specifies the wait time to receive response from
                        remote host before triggering timeout exception
        :return: None
        """
        """Fetch file over scp/sftp from remote device"""
        ssh = self._connection.paramiko_conn._connect_uncached()
        if proto == 'scp':
            if not HAS_SCP:
                raise AnsibleError("Required library scp is not installed.  Please install it using `pip install scp`")
            with SCPClient(ssh.get_transport(), socket_timeout=timeout) as scp:
                scp.get(source, destination)
        elif proto == 'sftp':
            with ssh.open_sftp() as sftp:
                sftp.get(source, destination)

    def get_diff(self, candidate=None, running=None, diff_match=None, diff_ignore_lines=None, path=None, diff_replace=None):
        """
        Generate diff between candidate and running configuration. If the
        remote host supports onbox diff capabilities ie. supports_onbox_diff in that case
        candidate and running configurations are not required to be passed as argument.
        In case if onbox diff capability is not supported candidate argument is mandatory
        and running argument is optional.
        :param candidate: The configuration which is expected to be present on remote host.
        :param running: The base configuration which is used to generate diff.
        :param diff_match: Instructs how to match the candidate configuration with current device configuration
                      Valid values are 'line', 'strict', 'exact', 'none'.
                      'line' - commands are matched line by line
                      'strict' - command lines are matched with respect to position
                      'exact' - command lines must be an equal match
                      'none' - will not compare the candidate configuration with the running configuration
        :param diff_ignore_lines: Use this argument to specify one or more lines that should be
                                  ignored during the diff.  This is used for lines in the configuration
                                  that are automatically updated by the system.  This argument takes
                                  a list of regular expressions or exact line matches.
        :param path: The ordered set of parents that uniquely identify the section or hierarchy
                     the commands should be checked against.  If the parents argument
                     is omitted, the commands are checked against the set of top
                    level or global commands.
        :param diff_replace: Instructs on the way to perform the configuration on the device.
                        If the replace argument is set to I(line) then the modified lines are
                        pushed to the device in configuration mode.  If the replace argument is
                        set to I(block) then the entire command block is pushed to the device in
                        configuration mode if any line is not correct.
        :return: Configuration and/or banner diff in json format.
               {
                   'config_diff': ''
               }

        """
        pass

    def run_commands(self, commands=None, check_rc=True):
        """
        Execute a list of commands on remote host and return the list of response
        :param commands: The list of command that needs to be executed on remote host.
                The individual command in list can either be a command string or command dict.
                If the command is dict the valid keys are
                {
                    'command': <command to be executed>
                    'prompt': <expected prompt on executing the command>,
                    'answer': <answer for the prompt>,
                    'output': <the format in which command output should be rendered eg: 'json', 'text'>,
                    'sendonly': <Boolean flag to indicate if it command execution response should be ignored or not>
                }
        :param check_rc: Boolean flag to check if returned response should be checked for error or not.
                         If check_rc is False the error output is appended in return response list, else if the
                         value is True an exception is raised.
        :return: List of returned response
        """
        pass

    def check_edit_config_capabiltiy(self, operations, candidate=None, commit=True, replace=None, comment=None):

        if not candidate and not replace:
            raise ValueError("must provide a candidate or replace to load configuration")

        if commit not in (True, False):
            raise ValueError("'commit' must be a bool, got %s" % commit)

        if replace and not operations['supports_replace']:
            raise ValueError("configuration replace is not supported")

        if comment and not operations.get('supports_commit_comment', False):
            raise ValueError("commit comment is not supported")

        if replace and not operations.get('supports_replace', False):
            raise ValueError("configuration replace is not supported")
