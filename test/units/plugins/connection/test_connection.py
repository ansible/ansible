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

from __future__ import annotations

from io import StringIO

import unittest
from ansible.playbook.play_context import PlayContext
from ansible.plugins.connection import ConnectionBase
from ansible.plugins.loader import become_loader


class NoOpConnection(ConnectionBase):

    @property
    def transport(self):
        """This method is never called by unit tests."""

    def _connect(self):
        """This method is never called by unit tests."""

    def exec_command(self):
        """This method is never called by unit tests."""

    def put_file(self):
        """This method is never called by unit tests."""

    def fetch_file(self):
        """This method is never called by unit tests."""

    def close(self):
        """This method is never called by unit tests."""


class TestConnectionBaseClass(unittest.TestCase):

    def setUp(self):
        self.play_context = PlayContext()
        self.play_context.prompt = (
            '[sudo via ansible, key=ouzmdnewuhucvuaabtjmweasarviygqq] password: '
        )
        self.in_stream = StringIO()

    def tearDown(self):
        pass

    def test_subclass_error(self):
        class ConnectionModule1(ConnectionBase):
            pass
        with self.assertRaises(TypeError):
            ConnectionModule1()  # pylint: disable=abstract-class-instantiated

    def test_subclass_success(self):
        self.assertIsInstance(NoOpConnection(self.play_context, self.in_stream), NoOpConnection)

    def test_check_password_prompt(self):
        local = (
            b'[sudo via ansible, key=ouzmdnewuhucvuaabtjmweasarviygqq] password: \n'
            b'BECOME-SUCCESS-ouzmdnewuhucvuaabtjmweasarviygqq\n'
        )

        ssh_pipelining_vvvv = b'''
debug3: mux_master_read_cb: channel 1 packet type 0x10000002 len 251
debug2: process_mux_new_session: channel 1: request tty 0, X 1, agent 1, subsys 0, term "xterm-256color", cmd "/bin/sh -c 'sudo -H -S  -p "[sudo via ansible, key=ouzmdnewuhucvuaabtjmweasarviygqq] password: " -u root /bin/sh -c '"'"'echo BECOME-SUCCESS-ouzmdnewuhucvuaabtjmweasarviygqq; /bin/true'"'"' && sleep 0'", env 0
debug3: process_mux_new_session: got fds stdin 9, stdout 10, stderr 11
debug2: client_session2_setup: id 2
debug1: Sending command: /bin/sh -c 'sudo -H -S  -p "[sudo via ansible, key=ouzmdnewuhucvuaabtjmweasarviygqq] password: " -u root /bin/sh -c '"'"'echo BECOME-SUCCESS-ouzmdnewuhucvuaabtjmweasarviygqq; /bin/true'"'"' && sleep 0'
debug2: channel 2: request exec confirm 1
debug2: channel 2: rcvd ext data 67
[sudo via ansible, key=ouzmdnewuhucvuaabtjmweasarviygqq] password: debug2: channel 2: written 67 to efd 11
BECOME-SUCCESS-ouzmdnewuhucvuaabtjmweasarviygqq
debug3: receive packet: type 98
'''  # noqa

        ssh_nopipelining_vvvv = b'''
debug3: mux_master_read_cb: channel 1 packet type 0x10000002 len 251
debug2: process_mux_new_session: channel 1: request tty 1, X 1, agent 1, subsys 0, term "xterm-256color", cmd "/bin/sh -c 'sudo -H -S  -p "[sudo via ansible, key=ouzmdnewuhucvuaabtjmweasarviygqq] password: " -u root /bin/sh -c '"'"'echo BECOME-SUCCESS-ouzmdnewuhucvuaabtjmweasarviygqq; /bin/true'"'"' && sleep 0'", env 0
debug3: mux_client_request_session: session request sent
debug3: send packet: type 98
debug1: Sending command: /bin/sh -c 'sudo -H -S  -p "[sudo via ansible, key=ouzmdnewuhucvuaabtjmweasarviygqq] password: " -u root /bin/sh -c '"'"'echo BECOME-SUCCESS-ouzmdnewuhucvuaabtjmweasarviygqq; /bin/true'"'"' && sleep 0'
debug2: channel 2: request exec confirm 1
debug2: exec request accepted on channel 2
[sudo via ansible, key=ouzmdnewuhucvuaabtjmweasarviygqq] password: debug3: receive packet: type 2
debug3: Received SSH2_MSG_IGNORE
debug3: Received SSH2_MSG_IGNORE

BECOME-SUCCESS-ouzmdnewuhucvuaabtjmweasarviygqq
debug3: receive packet: type 98
'''  # noqa

        ssh_novvvv = (
            b'[sudo via ansible, key=ouzmdnewuhucvuaabtjmweasarviygqq] password: \n'
            b'BECOME-SUCCESS-ouzmdnewuhucvuaabtjmweasarviygqq\n'
        )

        dns_issue = (
            b'timeout waiting for privilege escalation password prompt:\n'
            b'sudo: sudo: unable to resolve host tcloud014\n'
            b'[sudo via ansible, key=ouzmdnewuhucvuaabtjmweasarviygqq] password: \n'
            b'BECOME-SUCCESS-ouzmdnewuhucvuaabtjmweasarviygqq\n'
        )

        nothing = b''

        in_front = b'''
debug1: Sending command: /bin/sh -c 'sudo -H -S  -p "[sudo via ansible, key=ouzmdnewuhucvuaabtjmweasarviygqq] password: " -u root /bin/sh -c '"'"'echo
'''

        c = NoOpConnection(self.play_context, self.in_stream)
        c.set_become_plugin(become_loader.get('sudo'))
        c.become.prompt = '[sudo via ansible, key=ouzmdnewuhucvuaabtjmweasarviygqq] password: '

        self.assertTrue(c.become.check_password_prompt(local))
        self.assertTrue(c.become.check_password_prompt(ssh_pipelining_vvvv))
        self.assertTrue(c.become.check_password_prompt(ssh_nopipelining_vvvv))
        self.assertTrue(c.become.check_password_prompt(ssh_novvvv))
        self.assertTrue(c.become.check_password_prompt(dns_issue))
        self.assertFalse(c.become.check_password_prompt(nothing))
        self.assertFalse(c.become.check_password_prompt(in_front))
