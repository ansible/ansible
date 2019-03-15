# Based on the winrm connection plugin by Chris Church
#
# Copyright: (c) 2018, Pat Sharkey <psharkey@cleo.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
author:
- Pat Sharkey (@psharkey) <psharkey@cleo.com>
connection: aws_ssm_powershell
short_description: execute via AWS Systems Manager
description:
- This connection plugin allows ansible to execute tasks on an EC2 instance via the aws ssm CLI.
version_added: "2.8"
requirements:
- The remote EC2 instance must be running the AWS Systems Manager Agent (SSM Agent).
- The control machine must have the aws session manager plugin installed.
- The remote EC2 instance must have the curl installed.
options:
  instance_id:
    description: The EC2 instance ID.
    vars:
    - name: instance_id
    - name: aws_instance_id
  region:
    description: The region the EC2 instance is located.
    vars:
    - name: region
    - name: aws_region
    default: 'us-east-1'
  bucket_name:
    description: The name of the S3 bucket used for file transfers.
    vars:
    - name: bucket_name
  plugin:
    description: This defines the location of the session-manager-plugin binary.
    vars:
    - name: session_manager_plugin
    default: '/usr/local/bin/session-manager-plugin'
  retries:
    description: Number of attempts to connect.
    default: 3
    type: integer
    vars:
    - name: ansible_ssm_retries
  timeout:
    description: Connection timeout seconds.
    default: 60
    type: integer
    vars:
    - name: ansible_ssm_timeout
"""

from ansible.plugins.connection.aws_ssm import Connection as AwsSsmConnection


class Connection(AwsSsmConnection):
    ''' AWS SSM based connections for powershell '''

    transport = 'aws_ssm_powershell'
    module_implementation_preferences = ('.ps1', '.exe', '')

    def __init__(self, *args, **kwargs):

        self.protocol = None
        self.shell_id = None
        self.delegate = None
        self._shell_type = 'powershell'

        super(Connection, self).__init__(*args, **kwargs)

    def _prepare_terminal(self):
        ''' perform any one-time terminal settings '''

    def _wrap_command(self, cmd, sudoable, mark_start, mark_end):
        ''' wrap commad so stdout and status can be extracted '''

        return cmd + "; echo $?; echo '" + mark_start + "'\n" + "echo '" + mark_end + "'\n"

    def _post_process(self, stdout):
        ''' extract command status and strip anything following '''

        success = stdout.rfind('True')
        fail = stdout.rfind('False')

        if success > fail:
            returncode = 0
            stdout = stdout[:success]
        elif fail > success:
            try:
                # test using: ansible -m raw -a 'cmd /c exit 99'
                returncode = int(stdout[fail:].split()[1])
            except (IndexError, ValueError):
                returncode = -1
            stdout = stdout[:fail]
        else:
            returncode = -51

        # Strip sequence at terminal width
        if len(stdout) > 200:
            stdout = stdout.replace('\r\r\n', '')

        return (returncode, stdout)
