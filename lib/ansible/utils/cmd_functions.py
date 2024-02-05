# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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

import os
import select
import shlex
import subprocess
import sys

from ansible.module_utils.common.text.converters import to_bytes


def run_cmd(cmd, live=False, readsize=10):
    cmdargs = shlex.split(cmd)

    # subprocess should be passed byte strings.
    cmdargs = [to_bytes(a, errors='surrogate_or_strict') for a in cmdargs]

    p = subprocess.Popen(cmdargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout = b''
    stderr = b''
    rpipes = [p.stdout, p.stderr]
    while True:
        rfd, wfd, efd = select.select(rpipes, [], rpipes, 1)

        if p.stdout in rfd:
            dat = os.read(p.stdout.fileno(), readsize)
            if live:
                sys.stdout.buffer.write(dat)
            stdout += dat
            if dat == b'':
                rpipes.remove(p.stdout)
        if p.stderr in rfd:
            dat = os.read(p.stderr.fileno(), readsize)
            stderr += dat
            if live:
                sys.stdout.buffer.write(dat)
            if dat == b'':
                rpipes.remove(p.stderr)
        # only break out if we've emptied the pipes, or there is nothing to
        # read from and the process has finished.
        if (not rpipes or not rfd) and p.poll() is not None:
            break
        # Calling wait while there are still pipes to read can cause a lock
        elif not rpipes and p.poll() is None:
            p.wait()

    return p.returncode, stdout, stderr
