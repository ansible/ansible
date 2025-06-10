# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import os
import typing as t

from ansible.module_utils.common import warnings as _warnings

from ansible.module_utils.facts.collector import BaseFactCollector


class EnvFactCollector(BaseFactCollector):
    name = 'env'
    _fact_ids = set()  # type: t.Set[str]

    def collect(self, module=None, collected_facts=None):
        env_facts = {}
        env_facts['env'] = {}

        for k, v in os.environ.items():
            env_facts['env'][k] = v

        return env_facts


def __getattr__(importable_name):
    """Inject import-time deprecation warnings."""
    if importable_name == "iteritems":
        import importlib
        importable = getattr(
            importlib.import_module("ansible.module_utils.six"),
            importable_name
        )
    else:
        raise AttributeError(
            f"Cannot import name {importable_name!r} from {__name__!r} ({__file__!r})"
        )

    _warnings.deprecate(
        msg=f"Importing {importable_name!r} from {__name__!r} is deprecated.",
        version="2.23",
    )
    return importable
