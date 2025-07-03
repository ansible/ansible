# (c) 2020 Matt Martz <matt@sivel.net>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

"""
This file provides ease of use shortcuts for loading and dumping YAML,
preferring the YAML compiled C extensions to reduce duplicated code.
"""

from __future__ import annotations as _annotations

import collections.abc as _c
import typing as _t

from functools import partial as _partial

from .._internal import _datatag

HAS_LIBYAML = False

try:
    import yaml as _yaml
except ImportError:
    HAS_YAML = False
else:
    HAS_YAML = True

# DTFIX-FUTURE: refactor this to share the implementation with the controller version
#              use an abstract base class, with __init_subclass__ for representer registration, and instance methods for overridable representers
#              then tests can be consolidated instead of having two nearly identical copies

if HAS_YAML:
    try:
        from yaml import CSafeLoader as SafeLoader
        from yaml import CSafeDumper as SafeDumper
        from yaml.representer import SafeRepresenter
        from yaml.cyaml import CParser as Parser  # type: ignore[attr-defined]  # pylint: disable=unused-import

        HAS_LIBYAML = True
    except (ImportError, AttributeError):
        from yaml import SafeLoader  # type: ignore[assignment]
        from yaml import SafeDumper  # type: ignore[assignment]
        from yaml.representer import SafeRepresenter  # type: ignore[assignment]
        from yaml.parser import Parser  # type: ignore[assignment]  # pylint: disable=unused-import

    class _AnsibleDumper(SafeDumper):
        pass

    def _represent_ansible_tagged_object(self, data: _datatag.AnsibleTaggedObject) -> _t.Any:
        return self.represent_data(_datatag.AnsibleTagHelper.as_native_type(data))

    def _represent_tripwire(self, data: _datatag.Tripwire) -> _t.NoReturn:
        data.trip()

    _AnsibleDumper.add_multi_representer(_datatag.AnsibleTaggedObject, _represent_ansible_tagged_object)

    _AnsibleDumper.add_multi_representer(_datatag.Tripwire, _represent_tripwire)
    _AnsibleDumper.add_multi_representer(_c.Mapping, SafeRepresenter.represent_dict)
    _AnsibleDumper.add_multi_representer(_c.Sequence, SafeRepresenter.represent_list)

    yaml_load = _partial(_yaml.load, Loader=SafeLoader)
    yaml_load_all = _partial(_yaml.load_all, Loader=SafeLoader)

    yaml_dump = _partial(_yaml.dump, Dumper=_AnsibleDumper)
    yaml_dump_all = _partial(_yaml.dump_all, Dumper=_AnsibleDumper)
else:
    SafeLoader = object  # type: ignore[assignment,misc]
    SafeDumper = object  # type: ignore[assignment,misc]
    Parser = object  # type: ignore[assignment,misc]

    yaml_load = None  # type: ignore[assignment]
    yaml_load_all = None  # type: ignore[assignment]
    yaml_dump = None  # type: ignore[assignment]
    yaml_dump_all = None  # type: ignore[assignment]
