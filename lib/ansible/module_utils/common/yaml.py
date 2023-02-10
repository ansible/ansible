# (c) 2020 Matt Martz <matt@sivel.net>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

"""
This file provides ease of use shortcuts for loading and dumping YAML,
preferring the YAML compiled C extensions to reduce duplicated code.
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from functools import partial as _partial

HAS_LIBYAML = False

try:
    import yaml as _yaml
except ImportError:
    HAS_YAML = False
else:
    HAS_YAML = True

if HAS_YAML:
    try:
        from yaml import CSafeLoader as SafeLoader
        from yaml import CSafeDumper as SafeDumper
        from yaml.cyaml import CParser as Parser  # type: ignore[attr-defined]  # pylint: disable=unused-import

        HAS_LIBYAML = True
    except (ImportError, AttributeError):
        from yaml import SafeLoader  # type: ignore[assignment]
        from yaml import SafeDumper  # type: ignore[assignment]
        from yaml.parser import Parser  # type: ignore[assignment]  # pylint: disable=unused-import

    yaml_load = _partial(_yaml.load, Loader=SafeLoader)
    yaml_load_all = _partial(_yaml.load_all, Loader=SafeLoader)

    yaml_dump = _partial(_yaml.dump, Dumper=SafeDumper)
    yaml_dump_all = _partial(_yaml.dump_all, Dumper=SafeDumper)
else:
    SafeLoader = object  # type: ignore[assignment,misc]
    SafeDumper = object  # type: ignore[assignment,misc]
    Parser = object  # type: ignore[assignment,misc]

    yaml_load = None  # type: ignore[assignment]
    yaml_load_all = None  # type: ignore[assignment]
    yaml_dump = None  # type: ignore[assignment]
    yaml_dump_all = None  # type: ignore[assignment]
