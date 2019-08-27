"""Tests for validate-modules regexes."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from validate_modules.main import TYPE_REGEX


@pytest.mark.parametrize('cstring,cexpected', [
    ['if type(foo) is Bar', True],
    ['if Bar is type(foo)', True],
    ['if type(foo) is not Bar', True],
    ['if Bar is not type(foo)', True],
    ['if type(foo) == Bar', True],
    ['if Bar == type(foo)', True],
    ['if type(foo)==Bar', True],
    ['if Bar==type(foo)', True],
    ['if type(foo) != Bar', True],
    ['if Bar != type(foo)', True],
    ['if type(foo)!=Bar', True],
    ['if Bar!=type(foo)', True],
    ['if foo or type(bar) != Bar', True],
    ['x = type(foo)', False],
    ["error = err.message + ' ' + str(err) + ' - ' + str(type(err))", False],
    # cloud/amazon/ec2_group.py
    ["module.fail_json(msg='Invalid rule parameter type [%s].' % type(rule))", False],
    # files/patch.py
    ["p = type('Params', (), module.params)", False],  # files/patch.py
    # system/osx_defaults.py
    ["if self.current_value is not None and not isinstance(self.current_value, type(self.value)):", True],
    # system/osx_defaults.py
    ['raise OSXDefaultsException("Type mismatch. Type in defaults: " + type(self.current_value).__name__)', False],
    # network/nxos/nxos_interface.py
    ["if get_interface_type(interface) == 'svi':", False],
])
def test_type_regex(cstring, cexpected):  # type: (str, str) -> None
    """Check TYPE_REGEX against various examples to verify it correctly matches or does not match."""
    match = TYPE_REGEX.match(cstring)
    if cexpected and not match:
        assert False, "%s should have matched" % cstring
    elif not cexpected and match:
        assert False, "%s should not have matched" % cstring
