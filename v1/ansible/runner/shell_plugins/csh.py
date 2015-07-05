# (c) 2014, Chris Church <chris@ninemoreminutes.com>
#
# This file is part of Ansible.
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

from ansible.runner.shell_plugins.sh import ShellModule as ShModule

class ShellModule(ShModule):

    # How to end lines in a python script one-liner
    _SHELL_EMBEDDED_PY_EOL = '\\\n'

    def env_prefix(self, **kwargs):
        return 'env %s' % super(ShellModule, self).env_prefix(**kwargs)
