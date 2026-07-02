from __future__ import annotations

from ansible.plugins.action import ActionBase
from ansible.plugins import loader


class ActionModule(ActionBase):
    TRANSFERS_FILES = False
    _VALID_ARGS = frozenset(('type', 'name'))

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(None, task_vars)

        plugin_type = self._task.args.get('type')
        name = self._task.args.get('name')

        result = dict(changed=False, collection_list=self._task.collections)

        if all([plugin_type, name]):
            attr_name = '{0}_loader'.format(plugin_type)

            typed_loader = getattr(loader, attr_name, None)

            if not typed_loader:
                return (dict(failed=True, msg='invalid plugin type {0}'.format(plugin_type)))

            context = typed_loader.find_plugin_with_context(name, collection_list=self._task.collections)

            if not context.resolved:
                result['plugin_path'] = None
                result['redirect_list'] = []
            else:
                result['plugin_path'] = context.plugin_resolved_path
                result['redirect_list'] = context.redirect_list

        return result
