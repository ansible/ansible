# Copyright: (c) 2026, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import dataclasses
import typing as t


@dataclasses.dataclass
class Data:
    value: t.Any


def dataclass_asdict(value: t.Any) -> dict[str, t.Any]:
    return dataclasses.asdict(Data(value))


def dataclass_astuple(value: t.Any) -> tuple[t.Any]:
    return dataclasses.astuple(Data(value))


class FilterModule:
    def filters(self) -> dict[str, t.Callable]:
        return dict(dataclass_asdict=dataclass_asdict, dataclass_astuple=dataclass_astuple)
