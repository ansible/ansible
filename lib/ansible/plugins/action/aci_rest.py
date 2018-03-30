from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
from ansible.plugins.action import ActionBase
from ansible.module_utils._text import to_text


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):

        src = self._task.args.get('src', None)
        if src:
            try:
                self._handle_template()
            except (ValueError, AttributeError) as exc:
                return dict(failed=True, msg=exc.message)
        result = super(ActionModule, self).run(tmp=tmp, task_vars=task_vars)
        module_args = self._task.args.copy()
        module_return = self._execute_module(module_args=module_args,
                                             task_vars=task_vars, tmp=tmp)
        result.update(module_return)
        return result

    def _get_working_path(self):
        cwd = self._loader.get_basedir()
        if self._task._role is not None:
            cwd = self._task._role._role_path
        return cwd

    def _handle_template(self):
        src = self._task.args.get('src')
        working_path = self._get_working_path()

        if os.path.isabs(src):
            source = src
        else:
            source = self._loader.path_dwim_relative(
                working_path, 'templates', src)
            if not source:
                source = self._loader.path_dwim_relative(working_path, src)

        if not os.path.exists(source):
            raise ValueError('path specified in src not found')

        try:
            with open(source, 'r') as f:
                template_data = to_text(f.read())
        except IOError:
            return dict(failed=True, msg='unable to load src file')

        # Create a template search path in the following order:
        # [working_path, self_role_path, dependent_role_paths, dirname(source)]
        searchpath = [working_path]
        if self._task._role is not None:
            searchpath.append(self._task._role._role_path)
            if hasattr(self._task, "_block:"):
                dep_chain = self._task._block.get_dep_chain()
                if dep_chain is not None:
                    for role in dep_chain:
                        searchpath.append(role._role_path)
        searchpath.append(os.path.dirname(source))
        self._templar.environment.loader.searchpath = searchpath

        self._task.args['content'] = self._templar.template(template_data)
        # Now we have our template processed - we do not need src parameter, so we load parsed template into
        # the content parameter and delete the src one, as they are mutually exclusive
        del self._task.args['src']
