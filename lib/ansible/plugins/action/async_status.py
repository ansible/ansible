# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase
from ansible.utils.vars import merge_hash


class ActionModule(ActionBase):

    _VALID_ARGS = frozenset(('jid', 'mode'))

    def run(self, tmp=None, task_vars=None):
        results = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        if "jid" not in self._task.args:
            raise AnsibleError("jid is required")
        jid = self._task.args["jid"]
        mode = self._task.args.get("mode", "status")

        env_async_dir = [e for e in self._task.environment if
                         "ANSIBLE_ASYNC_DIR" in e]
        if len(env_async_dir) > 0:
            # for backwards compatibility we need to get the dir from
            # ANSIBLE_ASYNC_DIR that is defined in the environment. This is
            # deprecated and will be removed in favour of shell options
            async_dir = env_async_dir[0]['ANSIBLE_ASYNC_DIR']

            msg = "Setting the async dir from the environment keyword " \
                  "ANSIBLE_ASYNC_DIR is deprecated. Set the async_dir " \
                  "shell option instead"
            self._display.deprecated(msg, "2.12", collection_name='ansible.builtin')
        else:
            # inject the async directory based on the shell option into the
            # module args
            async_dir = self.get_shell_option('async_dir', default="~/.ansible_async")

        module_args = dict(jid=jid, mode=mode, _async_dir=async_dir)
        status = self._execute_module(module_name='ansible.legacy.async_status', task_vars=task_vars,
                                      module_args=module_args)
        results = merge_hash(results, status)
        return results
