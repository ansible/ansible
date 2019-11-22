from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase
from ansible.plugins import loader


class ActionModule(ActionBase):
    TRANSFERS_FILES = False
    _VALID_ARGS = frozenset(('type', 'name'))

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(None, task_vars)

        type = self._task.args.get('type')
        name = self._task.args.get('name')

        result = dict(changed=False, collection_list=self._task.collections)

        if all([type, name]):
            attr_name = '{0}_loader'.format(type)

            typed_loader = getattr(loader, attr_name, None)

            if not typed_loader:
                return (dict(failed=True, msg='invalid plugin type {0}'.format(type)))

            result['plugin_path'] = typed_loader.find_plugin(name, collection_list=self._task.collections)

        return result
