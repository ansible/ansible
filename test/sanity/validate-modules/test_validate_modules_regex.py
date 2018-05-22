# This is a standalone test for the regex inside validate-modules
# It is not suitable to add to the make tests target because the
# file under test is outside the test's sys.path AND has a hyphen
# in the name making it unimportable.
#
# To execute this by hand:
#   1) cd <checkoutdir>
#   2) source hacking/env-setup
#   3) PYTHONPATH=./lib nosetests -d -w test -v --nocapture sanity/validate-modules

import re
from ansible.compat.tests import unittest

# TYPE_REGEX = re.compile(r'.*\stype\(.*')
# TYPE_REGEX = re.compile(r'.*(if|or)\stype\(.*')
# TYPE_REGEX = re.compile(r'.*(if|or)(\s+.*|\s+)type\(.*')
# TYPE_REGEX = re.compile(r'.*(if|or)(\s+.*|\s+)type\(.*')
# TYPE_REGEX = re.compile(r'.*(if|\sor)(\s+.*|\s+)type\(.*')
# TYPE_REGEX =  re.compile(r'.*(if|\sor)(\s+.*|\s+)(?<!_)type\(.*')
TYPE_REGEX = re.compile(r'.*(if|or)(\s+.*|\s+)(?<!_)(?<!str\()type\(.*')


class TestValidateModulesRegex(unittest.TestCase):

    def test_type_regex(self):
        # each of these examples needs to be matched or not matched
        checks = [
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
        ]
        for idc, check in enumerate(checks):
            cstring = check[0]
            cexpected = check[1]

            match = TYPE_REGEX.match(cstring)
            if cexpected and not match:
                assert False, "%s should have matched" % cstring
            elif not cexpected and match:
                assert False, "%s should not have matched" % cstring
