"""This Python module calls deprecation functions in a variety of ways to validate call inference is supported in all common scenarios."""
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
name: deprecated
short_description: lookup
description: Lookup.
author:
  - Ansible Core Team
"""

EXAMPLES = """#"""
RETURN = """#"""

import ansible.utils.display
import ansible.module_utils.common.warnings

from ansible.module_utils import datatag
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import deprecate
from ansible.module_utils.common import warnings
from ansible.module_utils.common.warnings import deprecate as basic_deprecate
from ansible.module_utils.datatag import deprecate_value
from ansible.plugins.lookup import LookupBase
from ansible.utils import display as x_display
from ansible.utils.display import Display as XDisplay
from ansible.utils.display import _display

global_display = XDisplay()
other_global_display = x_display.Display()
foreign_global_display = x_display._display

# extra lines below to allow for adding more imports without shifting the line numbers of the code that follows
#
#
#
#
#
#
#


class LookupModule(LookupBase):
    def run(self, **kwargs):
        return []


class MyModule(AnsibleModule):
    """A class."""

    do_deprecated = global_display.deprecated

    def my_method(self) -> None:
        """A method."""

        self.deprecate('', version='2.0.0', collection_name='ns.col')


def give_me_a_func():
    return global_display.deprecated


def do_stuff() -> None:
    """A function."""
    d1 = x_display.Display()
    d2 = XDisplay()

    MyModule.do_deprecated('', version='2.0.0', collection_name='ns.col')
    basic_deprecate('', version='2.0.0', collection_name='ns.col')
    ansible.utils.display._display.deprecated('', version='2.0.0', collection_name='ns.col')
    d1.deprecated('', version='2.0.0', collection_name='ns.col')
    d2.deprecated('', version='2.0.0', collection_name='ns.col')
    x_display.Display().deprecated('', version='2.0.0', collection_name='ns.col')
    XDisplay().deprecated('', version='2.0.0', collection_name='ns.col')
    warnings.deprecate('', version='2.0.0', collection_name='ns.col')
    deprecate('', version='2.0.0', collection_name='ns.col')
    datatag.deprecate_value("thing", '', collection_name='ns.col', version='2.0.0')
    deprecate_value("thing", '', collection_name='ns.col', version='2.0.0')
    global_display.deprecated('', version='2.0.0', collection_name='ns.col')
    other_global_display.deprecated('', version='2.0.0', collection_name='ns.col')
    foreign_global_display.deprecated('', version='2.0.0', collection_name='ns.col')
    _display.deprecated('', version='2.0.0', collection_name='ns.col')
    give_me_a_func()("hello")  # not detected
