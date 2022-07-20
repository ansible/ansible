# -*- coding: utf-8 -*-
# (c) 2015, Brian Coca  <briancoca+dev@gmail.com>
# (c) 2018, Matt Martz  <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.errors import AnsibleError, AnsibleAction, _AnsibleActionDone, AnsibleActionFail
from ansible.module_utils._text import to_native
from ansible.module_utils.common.collections import Mapping, MutableMapping
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.module_utils.six import text_type
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    TRANSFERS_FILES = True

    def run(self, tmp=None, task_vars=None):
        self._supports_async = True

        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        body_format = self._task.args.get('body_format', 'raw')
        body = self._task.args.get('body')
        src = self._task.args.get('src', None)
        remote_src = boolean(self._task.args.get('remote_src', 'no'), strict=False)

        try:
            if remote_src:
                # everything is remote, so we just execute the module
                # without changing any of the module arguments
                # call with ansible.legacy prefix to prevent collections collisions while allowing local override
                raise _AnsibleActionDone(result=self._execute_module(module_name='ansible.legacy.uri',
                                                                     task_vars=task_vars, wrap_async=self._task.async_val))

            kwargs = {}

            if src:
                try:
                    src = self._find_needle('files', src)
                except AnsibleError as e:
                    raise AnsibleActionFail(to_native(e))

                tmp_src = self._connection._shell.join_path(self._connection._shell.tmpdir, os.path.basename(src))
                kwargs['src'] = tmp_src
                self._transfer_file(src, tmp_src)
                self._fixup_perms2((self._connection._shell.tmpdir, tmp_src))
            elif body_format == 'form-multipart':
                if not isinstance(body, Mapping):
                    raise AnsibleActionFail(
                        'body must be mapping, cannot be type %s' % body.__class__.__name__
                    )
                for field, value in body.items():
                    if not isinstance(value, MutableMapping):
                        continue
                    content = value.get('content')
                    filename = value.get('filename')
                    if not filename or content:
                        continue

                    try:
                        filename = self._find_needle('files', filename)
                    except AnsibleError as e:
                        raise AnsibleActionFail(to_native(e))

                    tmp_src = self._connection._shell.join_path(
                        self._connection._shell.tmpdir,
                        os.path.basename(filename)
                    )
                    value['filename'] = tmp_src
                    self._transfer_file(filename, tmp_src)
                    self._fixup_perms2((self._connection._shell.tmpdir, tmp_src))
                kwargs['body'] = body

            new_module_args = self._task.args | kwargs

            # call with ansible.legacy prefix to prevent collections collisions while allowing local override
            result.update(self._execute_module('ansible.legacy.uri', module_args=new_module_args, task_vars=task_vars, wrap_async=self._task.async_val))
        except AnsibleAction as e:
            result.update(e.result)
        finally:
            if not self._task.async_val:
                self._remove_tmp_path(self._connection._shell.tmpdir)
        return result
