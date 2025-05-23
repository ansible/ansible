from __future__ import annotations

from ansible.plugins.action import ActionBase
from ansible.module_utils.common.warnings import deprecate

from ..module_utils.shared_deprecation import get_deprecation_kwargs, get_deprecated_value


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        result = super().run(tmp, task_vars)

        for deprecate_kw in get_deprecation_kwargs():
            deprecate(**deprecate_kw)  # pylint: disable=ansible-deprecated-no-version

        result.update(deprecated_result=get_deprecated_value())

        return result
