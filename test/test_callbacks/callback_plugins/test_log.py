# (C) 2013, Michael Scherer, <misc@zarb.org>

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

import os


class CallbackModule(object):
    def playbook_on_play_start(self, foo):
        if os.path.exists('/tmp/ansible_test_disable'):
            self.disabled = True

    def playbook_on_stats(self, stats):
            open('/tmp/ansible_test_finish', 'w').close()
