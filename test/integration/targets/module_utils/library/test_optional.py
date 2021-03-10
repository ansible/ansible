#!/usr/bin/python
# Most of these names are only available via PluginLoader so pylint doesn't
# know they exist
# pylint: disable=no-name-in-module
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

# internal constants to keep pylint from griping about constant-valued conditionals
_private_false = False
_private_true = True

# module_utils import statements nested below any block are considered optional "best-effort" for AnsiballZ to include.
# test a number of different import shapes and nesting types to exercise this...

# first, some nested imports that should succeed...
try:
    from ansible.module_utils.urls import fetch_url as yep1
except ImportError:
    yep1 = None

try:
    import ansible.module_utils.common.text.converters as yep2
except ImportError:
    yep2 = None

try:
    # optional import from a legit collection
    from ansible_collections.testns.testcoll.plugins.module_utils.legit import importme as yep3
except ImportError:
    yep3 = None

# and a bunch that should fail to be found, but not break the module_utils payload build in the process...
try:
    from ansible.module_utils.bogus import fromnope1
except ImportError:
    fromnope1 = None

if _private_false:
    from ansible.module_utils.alsobogus import fromnope2
else:
    fromnope2 = None

try:
    import ansible.module_utils.verybogus
    nope1 = ansible.module_utils.verybogus
except ImportError:
    nope1 = None

# deepish nested with multiple block types- make sure the AST walker made it all the way down
try:
    if _private_true:
        if _private_true:
            if _private_true:
                if _private_true:
                    try:
                        import ansible.module_utils.stillbogus as nope2
                    except ImportError:
                        raise
except ImportError:
    nope2 = None

try:
    # optional import from a valid collection with an invalid package
    from ansible_collections.testns.testcoll.plugins.module_utils.bogus import collnope1
except ImportError:
    collnope1 = None

try:
    # optional import from a bogus collection
    from ansible_collections.bogusns.boguscoll.plugins.module_utils.bogus import collnope2
except ImportError:
    collnope2 = None

module = AnsibleModule(argument_spec={})

if not all([yep1, yep2, yep3]):
    module.fail_json(msg='one or more existing optional imports did not resolve')

if any([fromnope1, fromnope2, nope1, nope2, collnope1, collnope2]):
    module.fail_json(msg='one or more missing optional imports resolved unexpectedly')

module.exit_json(msg='all missing optional imports behaved as expected')
