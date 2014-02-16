# Copyright 2014, Lorin Hochstein <lorinh@gmail.com>
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
from multiprocessing import Process

def _follow_hook(runner, conn, stdout_path, stderr_path):
    """ Do a tail -f on stdout and stderr on remote and send to console """
    cmd = "tail -f %s& tail -f %s" % (stdout_path, stderr_path)
    runner._low_level_exec_command(conn, cmd, None, sudoable=False,
                                   capture_output=False)

class LiveOutput(object):
    def __init__(self, runner, conn, stdout_path, stderr_path):
        self.process = Process(
            target=_follow_hook,
            args=(runner, conn, stdout_path, stderr_path))

    def follow(self):
        self.process.start()

    def stop(self):
        self.process.terminate()