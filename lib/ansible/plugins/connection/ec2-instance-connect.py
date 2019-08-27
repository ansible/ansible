# Based on the ssh connection plugin by Austin Burnett
#
# (c) 2014, Lorin Hochstein
# (c) 2015, Leendert Brouwer (https://github.com/objectified)
# (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    connection: ec2_instance_connect
    short_description: leverage ec2 instance connect to send public key and connect via ssh client binary
    description:
        - This connection plugin allows ansible to send a public key to an ec2 instance to allow the use of SSH
    options:
      public_key:
          description: Public key to send to EC2 instance.
          default: ~/.ssh/id_rsa.pub
      remote_user:
          description: Instance username to authenticate as.
          type: string
          default: ec2-user
      availability_zone:
          description: AWS Availability Zone the instance is deployed in.
          type: string
          default: us-west-2a
'''

import os
from datetime import datetime
import subprocess

import boto3
from botocore.config import Config

from ansible.plugins.connection.ssh import Connection as SSHConnection
from ansible.plugins import get_plugin_class
from ansible.plugins.loader import connection_loader
from ansible import constants as C
from ansible.utils.display import Display

display = Display()


class Connection(SSHConnection):
    def __init__(self, play_context, new_stdin, *args, **kwargs):
        # Since we're overriding the SSH Connection module, it's not explicitly loaded
        # This was the most lightweight option to grab SSH config
        self._ssh = connection_loader.get('ssh', play_context, new_stdin, *args, **kwargs)
        ssh_options = C.config.get_plugin_options('connection', 'ssh')
        for k, v in ssh_options.items():
            setattr(play_context, k, v)

        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        # Grab the IP address for underlying SSH (instance ID required to send public key)
        self.instance_id = self._play_context.remote_addr
        ec2 = boto3.resource('ec2')
        instance = ec2.Instance(self.instance_id)
        self.host = instance.private_ip_address
        self.eic_client = boto3.client('ec2-instance-connect', config=Config(retries=dict(max_attempts=10)))
        self._play_context.ssh_args = '%s -o ControlPersist=yes' % self._play_context.ssh_args

    def get_option(self, option, hostvars=None):
        try:
            return super(Connection, self).get_option(option, hostvars=hostvars)
        except KeyError:
            return self._ssh.get_option(option, hostvars=hostvars)

    def _send_public_key(self):
        self.public_key = self.get_option('public_key')
        self.remote_user = self.get_option('remote_user')
        self.availability_zone = self.get_option('availability_zone')
        key = os.path.expanduser(self.public_key)
        with open(key, 'r') as f:
            res = self.eic_client.send_ssh_public_key(
                InstanceId=self.instance_id,
                InstanceOSUser=self.remote_user,
                AvailabilityZone=self.availability_zone,
                SSHPublicKey=f.read()
            )
            return res

    def _get_absolute_control_path(self):
        control_path_file = self._create_control_path(
            self.host,
            self.port,
            self.user
        )
        control_path = control_path_file % dict(directory=self.control_path_dir)
        return os.path.expanduser(control_path)

    def _connect(self):
        try:
            # this checks the status of the ControlPath to check that the socket is still open
            subprocess.check_call(['ssh', '-O', 'check', '-o', 'ControlPath=%s' % self._get_absolute_control_path(), self.host])
        except subprocess.CalledProcessError:
            display.vvv('refreshing public key')
            aws_response = self._send_public_key()
            if not aws_response['Success']:
                raise Exception('There was an error sending your public key.')
        super(Connection, self)._connect()
