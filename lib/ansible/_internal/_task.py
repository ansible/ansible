from __future__ import annotations

import dataclasses
import typing as t

from collections import abc as c

from ansible import constants
from ansible._internal._templating import _engine
from ansible._internal._templating._chain_templar import ChainTemplar
from ansible.errors import AnsibleError
from ansible.module_utils._internal._ambient_context import AmbientContextBase
from ansible.module_utils.datatag import native_type_name
from ansible.parsing import vault as _vault
from ansible.utils.display import Display

if t.TYPE_CHECKING:
    from ansible.playbook.task import Task


@dataclasses.dataclass
class TaskContext(AmbientContextBase):
    """Ambient context that wraps task execution on workers. It provides access to the currently executing task."""

    task: Task


TaskArgsFinalizerCallback = t.Callable[[str, t.Any, _engine.TemplateEngine, t.Any], t.Any]
"""Type alias for the shape of the `ActionBase.finalize_task_arg` method."""


class TaskArgsChainTemplar(ChainTemplar):
    """
    A ChainTemplar that carries a user-provided context object, optionally provided by `ActionBase.get_finalize_task_args_context`.
    TaskArgsFinalizer provides the context to each `ActionBase.finalize_task_arg` call to allow for more complex/stateful customization.
    """

    def __init__(self, *sources: c.Mapping, templar: _engine.TemplateEngine, callback: TaskArgsFinalizerCallback, context: t.Any) -> None:
        super().__init__(*sources, templar=templar)

        self.callback = callback
        self.context = context

    def template(self, key: t.Any, value: t.Any) -> t.Any:
        return self.callback(key, value, self.templar, self.context)


class TaskArgsFinalizer:
    """Invoked during task args finalization; allows actions to override default arg processing (e.g., templating)."""

    def __init__(self, *args: c.Mapping[str, t.Any] | str | None, templar: _engine.TemplateEngine) -> None:
        self._args_layers = [arg for arg in args if arg is not None]
        self._templar = templar

    def finalize(self, callback: TaskArgsFinalizerCallback, context: t.Any) -> dict[str, t.Any]:
        resolved_layers: list[c.Mapping[str, t.Any]] = []

        for layer in self._args_layers:
            if isinstance(layer, (str, _vault.EncryptedString)):  # EncryptedString can hide a template
                if constants.config.get_config_value('INJECT_FACTS_AS_VARS'):
                    Display().warning(
                        "Using a template for task args is unsafe in some situations "
                        "(see https://docs.ansible.com/ansible/devel/reference_appendices/faq.html#argsplat-unsafe).",
                        obj=layer,
                    )

                resolved_layer = self._templar.resolve_to_container(layer, options=_engine.TemplateOptions(value_for_omit={}))
            else:
                resolved_layer = layer

            if not isinstance(resolved_layer, dict):
                raise AnsibleError(f'Task args must resolve to a {native_type_name(dict)!r} not {native_type_name(resolved_layer)!r}.', obj=layer)

            resolved_layers.append(resolved_layer)

        ct = TaskArgsChainTemplar(*reversed(resolved_layers), templar=self._templar, callback=callback, context=context)

        return ct.as_dict()
