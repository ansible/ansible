from __future__ import annotations

import contextlib as _contextlib
import dataclasses as _dataclasses
from importlib import resources as _importlib_resources, util as _importlib_util
import inspect as _inspect
import pathlib as _pathlib
import typing as _t

if _t.TYPE_CHECKING:
    from ansible.module_utils.compat.typing import LiteralString


class EmbedManager:
    @classmethod
    def embed(cls, package: LiteralString, resource: LiteralString, /) -> EmbeddedResource:
        # TODO: register for runtime sniffing too
        if package.startswith('.'):
            st = _inspect.stack()
            sp = _importlib_util.find_spec(st[1].frame.f_globals['__name__'])
            package = _importlib_util.resolve_name(package, sp.parent)
        return EmbeddedResource(package, resource)


@_dataclasses.dataclass(frozen=True)
class EmbeddedResource:
    package: str
    resource: str

    @property
    def path_context_manager(self) -> _contextlib.AbstractContextManager[_pathlib.Path]:
        return _importlib_resources.path(self.package, self.resource)

    @property
    def python_module_ref(self) -> str:
        import pathlib
        return self.package + "." + str(pathlib.Path(self.resource).with_suffix(''))
