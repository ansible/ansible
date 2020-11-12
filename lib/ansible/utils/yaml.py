# (c) 2020 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""
This file provides ease of use shortcuts for loading and dumping YAML,
preferring the YAML compiled C extensions to reduce duplicated code.
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from functools import partial

import yaml

try:
    SafeLoader = yaml.CSafeLoader
    SafeDumper = yaml.CSafeDumper
    Parser = yaml.CParser
    HAS_LIBYAML = True
except AttributeError:
    SafeLoader = yaml.SafeLoader
    SafeDumper = yaml.SafeDumper
    Parser = yaml.Parser
    HAS_LIBYAML = False


safe_load = partial(yaml.load, Loader=SafeLoader)
safe_load_all = partial(yaml.load_all, Loader=SafeLoader)

safe_dump = partial(yaml.dump, Dumper=SafeDumper)
safe_dump_all = partial(yaml.dump_all, Dumper=SafeDumper)
