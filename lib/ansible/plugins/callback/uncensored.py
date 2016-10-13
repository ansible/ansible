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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from ansible.plugins.callback.default import CallbackModule as DefaultCallbackModule


class CallbackModule(DefaultCallbackModule):
    '''
    This is the like the default callback interface, which simply prints messages
    to stdout when new callback events are received. Except this callback doesn't
    censor them. That may include no_log items, internal task results keys, diff content,
    exception info, passwords, adult themes, private keys, the name of your favorite
    pet, the real identity of D.B. Cooper, strong language, etc.

    Warning: The following content may contain elements that are not suitable
             for some audiences. Viewer discretion is advised.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'uncensored'

    def _clean_results(self, result, task_name):
        pass

    def _get_item(self, result):
        # TODO: Decide if using the _ansible_item_label is 'censored'
        if result.get('_ansible_item_label', False):
            item = result.get('_ansible_item_label')
        else:
            item = result.get('item', None)

        return item

    def _dump_results(self, result, indent=None, sort_keys=True, keep_invocation=False):
        indent = indent or 4

        return json.dumps(result, indent=indent, ensure_ascii=False, sort_keys=sort_keys)

    def _handle_warnings(self, res):
        for warning in res.get('warnings', []):
            self._display.warning(warning)
