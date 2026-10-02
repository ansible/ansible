# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()


class ActionModule(ActionBase):
    """ Print statements during execution """

    TRANSFERS_FILES = False
    _VALID_ARGS = frozenset(('msg', 'channel'))
    _VALID_CHANNELS = frozenset(('deprecated', 'warning', 'display', 'verbose', 'error', 'callback', 'log'))

    def run(self, tmp=None, task_vars=None):

        result = super(ActionModule, self).run(tmp, task_vars)
        result['failed'] = True

        try:
            msg = self._task.args['msg']
        except KeyError:
            result['msg'] = "The required field 'msg' is missing"
            return result

        channel = self._task.args.get('channel', 'callback')

        if channel not in self._VALID_CHANNELS:
            result['msg'] = f"Invalid channel '{channel}', valid values are: {','.join(self._VALID_CHANNELS)}"
            return result

        if channel == 'callback':
            result['msg'] = msg
            result['_ansible_verbose_override'] = True
            result['_ansible_always_verbose'] = True
        else:
            call = getattr(display, channel)
            try:
                call(str(msg, errors='strict'))
            except UnicodeError as e:
                result['msg'] = f"Could not convert msg to unicode: {e!r}"
                return result

        result['failed'] = False
        return result
