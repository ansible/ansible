# Copyright: (c) 2025, Eero Aaltonen
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import annotations

import os
import shutil
import tempfile

import pgpy

from ansible import constants as C

from ansible.config.manager import ensure_type
from ansible.errors import AnsibleAction, AnsibleActionFail, AnsibleError
from ansible.module_utils.common.text.converters import to_bytes, to_text, to_native
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.action import ActionBase
from ansible.module_utils.six import string_types


class ActionModule(ActionBase):

    TRANSFERS_FILES = True

    def run(self, tmp=None, task_vars=None):
        """ Install PGP keyrings in binary format """

        if task_vars is None:
            task_vars = dict()

        super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        # Options type validation
		# strings
        for s_type in ('src', 'dest'):
            if s_type in self._task.args:
                value = ensure_type(self._task.args[s_type], 'string')
                if value is not None and not isinstance(value, str):
                    raise AnsibleActionFail("%s is expected to be a string, but got %s instead" % (s_type, type(value)))
                self._task.args[s_type] = value

        # booleans
        try:
            follow = boolean(self._task.args.get('follow', False), strict=False)
        except TypeError as e:
            raise AnsibleActionFail(to_native(e))

        # assign to local vars for ease of use
        source = self._task.args.get('src', None)
        dest = self._task.args.get('dest', None)

        try:
            # logical validation
            if source is None or dest is None:
                raise AnsibleActionFail("src and dest are required")

            try:
                # find in expected paths
                source = self._find_needle('files', source)
            except AnsibleError as ex:
                raise AnsibleActionFail(to_text(e))

                raise AnsibleActionFail(result=result) from ex

            try:
                key, _ = pgpy.PGPKey.from_file(source)
            except FileNotFoundError as e:
                raise AnsibleActionFail("could not find src=%s, %s" % (source, to_text(e)))
            except Exception as e:
                raise AnsibleActionFail("%s: %s" % (type(e).__name__, to_text(e)))

            new_task = self._task.copy()
            local_tempdir = tempfile.mkdtemp(dir=C.DEFAULT_LOCAL_TMP)

            try:
                result_file = os.path.join(local_tempdir, os.path.basename(source))
                with open(to_bytes(result_file, errors='surrogate_or_strict'), 'wb') as f:
                    f.write(bytes(key))

                new_task.args.update(
                    dict(
                        src=result_file,
                        dest=dest,
                        follow=follow,
                    ),
                )
                # call with ansible.legacy prefix to eliminate collisions with collections while still allowing local override
                copy_action = self._shared_loader_obj.action_loader.get('ansible.legacy.copy',
                                                                        task=new_task,
                                                                        connection=self._connection,
                                                                        play_context=self._play_context,
                                                                        loader=self._loader,
                                                                        templar=self._templar,
                                                                        shared_loader_obj=self._shared_loader_obj)
                return copy_action.run(task_vars=task_vars)
            finally:
                shutil.rmtree(to_bytes(local_tempdir, errors='surrogate_or_strict'))

        finally:
            self._remove_tmp_path(self._connection._shell.tmpdir)
