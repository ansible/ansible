# (c) 2015, Ansible Inc,
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

from ansible import constants as C
from ansible.errors import AnsibleActionFail
from ansible.executor.module_common import _apply_action_arg_defaults
from ansible.module_utils.facts.system.pkg_mgr import PKG_MGRS
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display
from ansible.utils.vars import combine_vars

display = Display()


class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    BUILTIN_PKG_MGR_MODULES = {manager['name'] for manager in PKG_MGRS}

    def run(self, tmp: str | None = None, task_vars: dict | None = None) -> dict:
        """ handler for package operations """

        self._supports_check_mode = True
        self._supports_async = True

        super(ActionModule, self).run(tmp, task_vars)

        action = self._task.args.get('use', 'auto')

        try:
            if action == 'auto':

                if self._task.delegate_to:
                    hosts_vars = task_vars['hostvars'][self._task.delegate_to]
                    tvars = combine_vars(self._task.vars, task_vars.get('delegated_vars', {}))
                else:
                    hosts_vars = task_vars
                    tvars = task_vars

                # use config
                action = tvars.get('ansible_package_use', None)

                if not action:
                    # no use, no config, get from facts
                    if hosts_vars.get('ansible_facts', {}).get('pkg_mgr', False):
                        facts = hosts_vars
                        pmgr = 'pkg_mgr'
                    else:
                        # we had no facts, so generate them
                        # very expensive step, we actually run fact gathering because we don't have facts for this host.
                        facts = self._execute_module(
                            module_name='ansible.legacy.setup',
                            module_args=dict(filter='ansible_pkg_mgr', gather_subset='!all'),
                            task_vars=task_vars,
                        )
                        if facts.get("failed", False):
                            raise AnsibleActionFail(
                                f"Failed to fetch ansible_pkg_mgr to determine the package action backend: {facts.get('msg')}",
                                result=facts,
                            )
                        pmgr = 'ansible_pkg_mgr'

                    try:
                        # actually get from facts
                        action = facts['ansible_facts'][pmgr]
                    except KeyError:
                        raise AnsibleActionFail('Could not detect a package manager. Try using the "use" option.')

            if action and action != 'auto':
                module_context = None

                # see if we use custom mapped, use orig if not
                action = C.PACKAGE_MANAGERS.get(action, action)
                # prefix with ansible.legacy to eliminate external collisions while still allowing library/ override
                if action in self.BUILTIN_PKG_MGR_MODULES:
                    action = f'ansible.legacy.{action}'

                # find what to execute, action plugins having priority
                has_action_plugin = self._shared_loader_obj.module_loader.has_plugin(action)
                if not has_action_plugin:
                    module_context = self._shared_loader_obj.module_loader.find_plugin_with_context(action, collection_list=self._task.collections)
                    if module_context and module_context.resolved and module_context.action_plugin:
                        # module itself specifies action plugin
                        action = module_context.action_plugin
                        has_action_plugin = True

                # prep to run he action
                new_module_args = self._task.args.copy()
                if 'use' in new_module_args:
                    del new_module_args['use']

                if has_action_plugin:
                    display.vvvv(f"Chose {action!r} action plugin")
                    new_task = new_task = self._task.copy()
                    new_task.args.update(new_module_args)
                    pkg_action, action_context = self._shared_loader_obj.action_loader.get_with_context(action,
                                                                                                        task=new_task,
                                                                                                        connection=self._connection,
                                                                                                        play_context=self._play_context,
                                                                                                        loader=self._loader,
                                                                                                        templar=self._templar,
                                                                                                        shared_loader_obj=self._shared_loader_obj)
                    if pkg_action:
                        display.vvvv(f"Running {action!r}")
                        return pkg_action.run(task_vars=task_vars)
                    else:
                        raise AnsibleActionFail(f"Failed to load {action!r}: {action_context!r}")
                elif module_context and module_context.resolved:
                    display.vvvv(f"Chose {action!r} module")
                    # get defaults for specific module
                    new_module_args = _apply_action_arg_defaults(module_context.resolved_fqcn, self._task, new_module_args, self._templar)


                    display.vvvv(f"Running {action!r}")
                    return self._execute_module(module_name=action, module_args=new_module_args, task_vars=task_vars, wrap_async=self._task.async_val)
            else:
                raise AnsibleActionFail('Could not detect which package manager to use. Try gathering facts or setting the "use" option.')
        finally:
            pass  # avoid de-dent all on refactor
