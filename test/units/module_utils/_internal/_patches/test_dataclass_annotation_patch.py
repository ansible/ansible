"""Test dataclass patching to verify ClassVar works properly."""

from __future__ import annotations

import dataclasses
import typing as t

from typing import ClassVar

from ansible.module_utils.compat import typing as typing_surrogate
from ansible.module_utils.compat.typing import ClassVar as ClassVarFromSurrogate
from ansible.module_utils._internal._datatag import _tag_dataclass_kwargs


def test_classvar_fields() -> None:
    """Verify that `typing.ClassVar` works with dataclasses."""
    @dataclasses.dataclass(**_tag_dataclass_kwargs)
    class ExerciseClassVar:
        real_local: ClassVar[int]
        real_from_module: t.ClassVar[int]
        surrogate_local: ClassVarFromSurrogate
        # this is the case that was actually broken; treated as an instance field when ClassVar was dot-referenced from a non-typing module
        surrogate_from_module: typing_surrogate.ClassVar[int]

        instance_field: int = 42

    fields = dataclasses.fields(ExerciseClassVar)

    assert len(fields) == 1
    assert ExerciseClassVar()

    # ensure that the classvars are all settable; some forms of the failure prevent this
    ExerciseClassVar.real_local = 42
    ExerciseClassVar.real_from_module = 42
    ExerciseClassVar.surrogate_local = 42
    ExerciseClassVar.surrogate_from_module = 42

    assert fields[-1].name == 'instance_field'
