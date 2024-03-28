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

from ansible import context, constants as C
from ansible.playbook.attribute import NonInheritableFieldAttribute
from ansible.playbook.task import Task
from ansible.module_utils.six import string_types
from ansible.utils.display import Display


display = Display()


class Handler(Task):

    listen = NonInheritableFieldAttribute(isa='list', default=list, listof=string_types, static=True)

    def __init__(self, block=None, role=None, task_include=None):
        self.notified_hosts = []

        self.cached_name = False

        super(Handler, self).__init__(block=block, role=role, task_include=task_include)

    def __repr__(self):
        ''' returns a human-readable representation of the handler '''
        return "HANDLER: %s" % self.get_name()

    @staticmethod
    def load(data, block=None, role=None, task_include=None, variable_manager=None, loader=None):
        t = Handler(block=block, role=role, task_include=task_include)
        return t.load_data(data, variable_manager=variable_manager, loader=loader)

    def _validate_tags(self, attr, name, value):
        if not value:
            setattr(self, name, ["always"])
            if C.HANDLERS_TAGS_COMPAT_WARNING and context.cliargs_deferred_get('tags')() != ("all",):
                # FIXME deprecate this behavior and match the functionality with regular tasks?
                display.warning(
                    "Since ansible-core 2.17 tags are supported on handlers. "
                    "There is at least one untagged handler in the play while the --tags "
                    "command line option is specified. For backwards compatibility any "
                    "untagged handler is implicitly tagged with the 'always' tag "
                    "and therefore ignores any tags specified in --tags. You can silence "
                    "this warning via the HANDLERS_TAGS_COMPAT_WARNING configuration option."
                )

    def notify_host(self, host):
        if not self.is_host_notified(host):
            self.notified_hosts.append(host)
            return True
        return False

    def remove_host(self, host):
        self.notified_hosts = [h for h in self.notified_hosts if h != host]

    def clear_hosts(self):
        self.notified_hosts = []

    def is_host_notified(self, host):
        return host in self.notified_hosts

    def serialize(self):
        result = super(Handler, self).serialize()
        result['is_handler'] = True
        return result
