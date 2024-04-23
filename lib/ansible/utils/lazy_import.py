# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


import contextlib
import importlib.util
import sys
import types


def lazy_import(name: str) -> types.ModuleType:
    with contextlib.suppress(KeyError):
        return sys.modules[name]

    if (spec := importlib.util.find_spec(name)) is None:
        raise ModuleNotFoundError(name)
    spec.loader = importlib.util.LazyLoader(spec.loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
