# (c) 2020 Matt Martz <matt@sivel.net>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

"""
This file provides ease of use shortcuts for loading and dumping YAML,
preferring the YAML compiled C extensions to reduce duplicated code.
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from functools import partial as _partial

import ansible.module_utils.compat.typing as t

HAS_LIBYAML = False
try:
    import yaml as _yaml
except ImportError:
    HAS_YAML = False
    SafeLoader = None
    SafeDumper = None
    Parser = None
    yaml_load = None
    yaml_load_all = None
    yaml_dump = None
    yaml_dump_all = None
else:
    HAS_YAML = True
    try:
        SafeLoader = _yaml.CSafeLoader
        SafeDumper = _yaml.CSafeDumper
        Parser = _yaml.cyaml.CParser
        HAS_LIBYAML = True
    except AttributeError:
        SafeLoader = _yaml.SafeLoader  # type: t.Type[_yaml.CSafeLoader] | t.Type[_yaml.SafeLoader]  # type: ignore[no-redef]
        SafeDumper = _yaml.SafeDumper  # type: t.Type[_yaml.CSafeDumper] | t.Type[_yaml.SafeDumper]  # type: ignore[no-redef]
        Parser = _yaml.parser.Parser  # type: t.Type[_yaml.cyaml.CParser] | t.Type[_yaml.parser.Parser]  # type: ignore[no-redef]

    yaml_load = _partial(_yaml.load, Loader=SafeLoader)
    yaml_load_all = _partial(_yaml.load_all, Loader=SafeLoader)

    yaml_dump = _partial(_yaml.dump, Dumper=SafeDumper)
    yaml_dump_all = _partial(_yaml.dump_all, Dumper=SafeDumper)
