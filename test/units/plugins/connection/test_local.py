#
# (c) 2020 Red Hat Inc.
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

import os
import stat
import subprocess
import tempfile
import textwrap
import unittest

from ansible.errors import AnsibleError
from ansible.plugins.connection import local
from ansible.playbook.play_context import PlayContext
from ansible.plugins.loader import become_loader, connection_loader, shell_loader


# Stub become_exe from https://github.com/ansible/ansible/issues/87934:
# always rejects the password, re-prompts once, then exits.
REJECT_STUB = textwrap.dedent("""\
    #!/bin/bash
    prompt=""
    while [ $# -gt 0 ]; do
      case "$1" in
        -p) prompt="$2"; shift 2 ;;
        -u) shift 2 ;;
        -H|-S|-n|-k|-E) shift ;;
        *) shift ;;
      esac
    done
    printf '%s ' "$prompt" >&2
    IFS= read -r _ || true
    printf 'Sorry, try again.\\n' >&2
    printf '%s ' "$prompt" >&2
    IFS= read -r _ || true
    exit 1
    """)

# Stub become_exe that accepts the password and runs the wrapped command.
ACCEPT_STUB = textwrap.dedent("""\
    #!/bin/bash
    prompt=""
    while [ $# -gt 0 ]; do
      case "$1" in
        -p) prompt="$2"; shift 2 ;;
        -u) shift 2 ;;
        -H|-S|-n|-k|-E) shift ;;
        *) break ;;
      esac
    done
    printf '%s ' "$prompt" >&2
    IFS= read -r _ || true
    exec "$@"
    """)


class TestLocalConnectionClass(unittest.TestCase):

    def test_local_connection_module(self):
        play_context = PlayContext()
        play_context.prompt = (
            '[sudo via ansible, key=ouzmdnewuhucvuaabtjmweasarviygqq] password: '
        )
        in_stream = StringIO()

        self.assertIsInstance(local.Connection(play_context, in_stream), local.Connection)

    def _run_become(self, stub_source):
        """Run _ensure_become_success against a stub become_exe, returning the Popen object."""
        tmpdir = tempfile.mkdtemp()
        stub_path = os.path.join(tmpdir, 'stub-become')
        with open(stub_path, 'w') as f:
            f.write(stub_source)
        os.chmod(stub_path, os.stat(stub_path).st_mode | stat.S_IXUSR)

        sudo = become_loader.get('sudo')
        sudo.set_options(direct={
            'become_exe': stub_path,
            'become_pass': 'wrongpassword',
            'become_flags': '-H -S',
        })
        sh = shell_loader.get('sh')
        sh.executable = '/bin/bash'
        cmd = sudo.build_become_command('/bin/true', sh)

        conn = connection_loader.get('local', PlayContext(), StringIO())
        conn.set_become_plugin(sudo)
        # set the options the plugin reads instead of relying on the config lookup
        conn.set_options(direct={'become_success_timeout': 10, 'become_strip_preamble': True})

        p = subprocess.Popen(
            cmd,
            shell=True,
            executable='/bin/sh',
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return conn, p

    def test_wrong_become_password_reported_as_incorrect(self):
        # https://github.com/ansible/ansible/issues/87934
        conn, p = self._run_become(REJECT_STUB)
        try:
            with self.assertRaisesRegex(AnsibleError, 'Incorrect sudo password'):
                conn._ensure_become_success(p, None, sudoable=True)
        finally:
            p.kill()
            p.wait()

    def test_correct_become_password_still_succeeds(self):
        conn, p = self._run_become(ACCEPT_STUB)
        try:
            conn._ensure_become_success(p, None, sudoable=True)
        finally:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait()
        self.assertEqual(p.returncode, 0)
