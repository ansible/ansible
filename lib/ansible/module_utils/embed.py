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
    """Utility class for embedding arbitrary content in an AnsiballZ payload."""
    @classmethod
    def embed(cls, package: LiteralString, resource: LiteralString, /) -> EmbeddedResource:
        """
        Request embedding of the specified `resource` from `package` in the generated AnsiballZ payload.
        The `package` argument must resolve to a Python package beneath `ansible` or `ansible_collections`.
        Relative import-style strings are supported (e.g. `..module_utils.something`).
        The `resource` argument must match the target filename.
        The method returns an `EmbeddedResource` object that must be stored and used to access the embedded content at runtime.

        To enable embedding analysis during payload build, the `embed` module must be imported in one of the following ways:
        `from ansible.module_utils.embed import EmbedManager` (optional alias supported)
        `from ansible.module_utils import embed` (optional alias supported)

        To be properly detected during payload build analysis, the `embed` call must:
        * Occur at the topmost level of a module or module_util.
        * Assign its result to a valid variable.
        * Use only inline literal string values as positional arguments.
        * Use only the as-imported name of the `embed` module or `EmbedManager` type (including import aliases).
        """
        if package.startswith('.'):
            st = _inspect.stack()
            sp = _importlib_util.find_spec(st[1].frame.f_globals['__name__'])
            package = _importlib_util.resolve_name(package, sp.parent)
            # FUTURE: register this value for runtime discovery of "what's embedded here"
        return EmbeddedResource(package, resource)


@_dataclasses.dataclass(frozen=True)
class EmbeddedResource:
    """Wrapper object returned by `EmbedManager.embed()` for runtime access to content embedded in an AnsiballZ payload."""
    package: str
    resource: str

    @property
    def path_context_manager(self) -> _contextlib.AbstractContextManager[_pathlib.Path]:
        """
        Returns a context manager that, once entered, provides a `pathlib.Path` to the embedded content.

        Path validity is only guaranteed until the context manager exits, as the temporarily extracted content is deleted when running from a zip archive.
        """
        return _importlib_resources.path(self.package, self.resource)

    @property
    def python_module_ref(self) -> str:
        """Returns a fully-qualified Python module reference to the embedded content (with the `.py` extension suppressed)."""
        return self.package + "." + str(_pathlib.Path(self.resource).with_suffix(''))
