# (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from io import StringIO

from ansible.compat.tests import mock
from ansible.compat.tests import unittest
from ansible.errors import AnsibleError
from ansible.playbook.play_context import PlayContext

from ansible.plugins.connection import ConnectionBase
#from ansible.plugins.connection.accelerate import Connection as AccelerateConnection
#from ansible.plugins.connection.chroot import Connection as ChrootConnection
#from ansible.plugins.connection.funcd import Connection as FuncdConnection
#from ansible.plugins.connection.jail import Connection as JailConnection
#from ansible.plugins.connection.libvirt_lxc import Connection as LibvirtLXCConnection
from ansible.plugins.connection.lxc import Connection as LxcConnection
from ansible.plugins.connection.local import Connection as LocalConnection
from ansible.plugins.connection.paramiko_ssh import Connection as ParamikoConnection
from ansible.plugins.connection.ssh import Connection as SSHConnection
from ansible.plugins.connection.docker import Connection as DockerConnection
#from ansible.plugins.connection.winrm import Connection as WinRmConnection
from ansible.plugins.connection.network_cli import Connection as NetworkCliConnection


class TestConnectionBaseClass(unittest.TestCase):

    def setUp(self):
        self.play_context = PlayContext()
        self.in_stream = StringIO()

    def tearDown(self):
        pass

    def test_subclass_error(self):
        class ConnectionModule1(ConnectionBase):
            pass
        with self.assertRaises(TypeError):
            ConnectionModule1()

        class ConnectionModule2(ConnectionBase):
            def get(self, key):
                super(ConnectionModule2, self).get(key)

        with self.assertRaises(TypeError):
            ConnectionModule2()

    def test_subclass_success(self):
        class ConnectionModule3(ConnectionBase):
            @property
            def transport(self):
                pass
            def _connect(self):
                pass
            def exec_command(self):
                pass
            def put_file(self):
                pass
            def fetch_file(self):
                pass
            def close(self):
                pass
        self.assertIsInstance(ConnectionModule3(self.play_context, self.in_stream), ConnectionModule3)

#    def test_accelerate_connection_module(self):
#        self.assertIsInstance(AccelerateConnection(), AccelerateConnection)
#
#    def test_chroot_connection_module(self):
#        self.assertIsInstance(ChrootConnection(), ChrootConnection)
#
#    def test_funcd_connection_module(self):
#        self.assertIsInstance(FuncdConnection(), FuncdConnection)
#
#    def test_jail_connection_module(self):
#        self.assertIsInstance(JailConnection(), JailConnection)
#
#    def test_libvirt_lxc_connection_module(self):
#        self.assertIsInstance(LibvirtLXCConnection(), LibvirtLXCConnection)

    def test_lxc_connection_module(self):
        self.assertIsInstance(LxcConnection(self.play_context, self.in_stream), LxcConnection)

    def test_local_connection_module(self):
        self.assertIsInstance(LocalConnection(self.play_context, self.in_stream), LocalConnection)

    def test_paramiko_connection_module(self):
        self.assertIsInstance(ParamikoConnection(self.play_context, self.in_stream), ParamikoConnection)

    def test_ssh_connection_module(self):
        self.assertIsInstance(SSHConnection(self.play_context, self.in_stream), SSHConnection)

    @mock.patch('ansible.plugins.connection.docker.Connection._old_docker_version', return_value=('false', 'garbage', '', 1))
    @mock.patch('ansible.plugins.connection.docker.Connection._new_docker_version', return_value=('docker version', '1.2.3', '', 0))
    def test_docker_connection_module_too_old(self, mock_new_docker_verison, mock_old_docker_version):
        self.assertRaisesRegexp(AnsibleError, '^docker connection type requires docker 1.3 or higher$',
                                DockerConnection, self.play_context, self.in_stream, docker_command='/fake/docker')

    @mock.patch('ansible.plugins.connection.docker.Connection._old_docker_version', return_value=('false', 'garbage', '', 1))
    @mock.patch('ansible.plugins.connection.docker.Connection._new_docker_version', return_value=('docker version', '1.3.4', '', 0))
    def test_docker_connection_module(self, mock_new_docker_verison, mock_old_docker_version):
        self.assertIsInstance(DockerConnection(self.play_context, self.in_stream, docker_command='/fake/docker'),
                              DockerConnection)

    # old version and new version fail
    @mock.patch('ansible.plugins.connection.docker.Connection._old_docker_version', return_value=('false', 'garbage', '', 1))
    @mock.patch('ansible.plugins.connection.docker.Connection._new_docker_version', return_value=('false', 'garbage', '', 1))
    def test_docker_connection_module_wrong_cmd(self, mock_new_docker_version, mock_old_docker_version):
        self.assertRaisesRegexp(AnsibleError, '^Docker version check (.*?) failed: ',
                                DockerConnection, self.play_context, self.in_stream, docker_command='/fake/docker')

#    def test_winrm_connection_module(self):
#        self.assertIsInstance(WinRmConnection(), WinRmConnection)

    def test_network_cli_connection_module(self):
        self.assertIsInstance(NetworkCliConnection(self.play_context, self.in_stream), NetworkCliConnection)
        self.assertIsInstance(NetworkCliConnection(self.play_context, self.in_stream), ParamikoConnection)
