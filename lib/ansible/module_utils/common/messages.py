from __future__ import annotations

import sys
import dataclasses

# deprecated: description='typing.Self exists in Python 3.11+' python_version='3.10'
from ..compat import typing as t

from ..datatag import AnsibleSerializableDataclass

if sys.version_info >= (3, 10):
    # Using slots for reduced memory usage and improved performance.
    _dataclass_kwargs = dict(frozen=True, kw_only=True, slots=True)
else:
    # deprecated: description='always use dataclass slots and keyword-only args' python_version='3.9'
    _dataclass_kwargs = dict(frozen=True)


@dataclasses.dataclass(**_dataclass_kwargs)
class Detail(AnsibleSerializableDataclass):
    """Message detail with optional source context and help text."""

    msg: str
    formatted_source_context: t.Optional[str] = None
    help_text: t.Optional[str] = None


@dataclasses.dataclass(**_dataclass_kwargs)
class SummaryBase(AnsibleSerializableDataclass):
    """Base class for an error/warning/deprecation summary with details (possibly derived from an exception __cause__ chain) and an optional traceback."""

    details: t.Tuple[Detail, ...]
    formatted_traceback: t.Optional[str] = None

    def format(self) -> str:
        """Returns a string representation of the warning details."""
        # DTFIX-RELEASE: should this borrow some of the message squashing features we use in get_chained_message?
        return ': '.join(detail.msg for detail in self.details)

    def _post_validate(self) -> None:
        if not self.details:
            raise ValueError(f'{type(self).__name__}.details cannot be empty')

    @classmethod
    def _from_details(cls, *details: Detail, formatted_traceback: t.Optional[str] = None, **kwargs) -> t.Self:
        """Utility factory method to avoid inline tuples."""
        return cls(details=details, formatted_traceback=formatted_traceback, **kwargs)


@dataclasses.dataclass(**_dataclass_kwargs)
class ErrorSummary(SummaryBase):
    """Error summary with details (possibly derived from an exception __cause__ chain) and an optional traceback."""


@dataclasses.dataclass(**_dataclass_kwargs)
class WarningSummary(SummaryBase):
    """Warning summary with details (possibly derived from an exception __cause__ chain) and an optional traceback."""


@dataclasses.dataclass(**_dataclass_kwargs)
class DeprecationSummary(WarningSummary):
    """Deprecation summary with details (possibly derived from an exception __cause__ chain) and an optional traceback."""

    version: t.Optional[str] = None
    date: t.Optional[str] = None
    collection_name: t.Optional[str] = None

    def _as_simple_dict(self) -> t.Dict[str, t.Any]:
        """Returns a dictionary representation of the deprecation object in the format exposed to playbooks."""
        result = self._as_dict()
        result.pop('details')
        result.update(msg=self.format())

        return result
