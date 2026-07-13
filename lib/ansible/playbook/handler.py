# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

from ansible.errors import AnsibleAssertionError
from ansible.playbook.attribute import NonInheritableFieldAttribute
from ansible.playbook.task import Task


class Handler(Task):

    listen = NonInheritableFieldAttribute(isa='list', default=list, listof=(str,), static=True)

    def __init__(self, block=None, role=None, task_include=None):
        self.notified_hosts = []

        self.cached_name = False

        super(Handler, self).__init__(block=block, role=role, task_include=task_include)

    def __repr__(self):
        """ returns a human-readable representation of the handler """
        return "HANDLER: %s" % self.get_name()

    def _validate_listen(self, attr, name, value):
        new_value = self.get_validated_value(name, attr, value, None)
        if self._role is not None:
            for listener in new_value.copy():
                new_value.extend([
                    f"{self._role.get_name(include_role_fqcn=True)} : {listener}",
                    f"{self._role.get_name(include_role_fqcn=False)} : {listener}",
                ])
        setattr(self, name, new_value)

    @staticmethod
    def load(data, block=None, role=None, task_include=None, variable_manager=None, loader=None):
        t = Handler(block=block, role=role, task_include=task_include)
        return t.load_data(data, variable_manager=variable_manager, loader=loader)

    def notify_host(self, host):
        if not self.is_host_notified(host):
            self.notified_hosts.append(host)
            return True
        return False

    def remove_host(self, host):
        try:
            self.notified_hosts.remove(host)
        except ValueError:
            raise AnsibleAssertionError(
                f"Attempting to remove a notification on handler '{self}' for host '{host}' but it has not been notified."
            )

    def clear_hosts(self):
        self.notified_hosts = []

    def is_host_notified(self, host):
        return host in self.notified_hosts
