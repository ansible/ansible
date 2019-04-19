#
# (c) 2019, Clay Curtis <jccurtis@presidio.com>
#
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys

from ansible.errors import AnsibleError, AnsibleFilterError
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.six import string_types
from ansible.utils.display import Display

try:
    from genie.conf.base import Device, Testbed
    from genie.libs.parser.utils import get_parser
    HAS_GENIE = True
except ImportError:
    HAS_GENIE = False

try:
    from pyats.datastructures import AttrDict
    HAS_PYATS = True
except ImportError:
    HAS_PYATS = False


display = Display()


def parse_genie(cli_output, command=None, os=None):
    """
    Uses the Cisco pyATS/Genie library to parse cli output into structured data.
    :param cli_output: (String) CLI output from Cisco device
    :param command: (String) CLI command that was used to generate the cli_output
    :param os: (String) Operating system of the device for which cli_output was obtained.
    :return: Dict object conforming to the defined genie parser schema.
             https://pubhub.devnetcloud.com/media/pyats-packages/docs/genie/genie_libs/#/parsers/show%20version
    """

    # Does the user have the necessary packages installed in order to use this filter?
    if not HAS_GENIE:
        raise AnsibleFilterError("parse_genie: Genie package is not installed. To install, run 'pip install genie'.")

    if not HAS_PYATS:
        raise AnsibleFilterError("parse_genie: pyATS package is not installed. To install, run 'pip install pyats'.")

    # Does the user have the required version of Python 3.4 that Genie and pyATS requires?
    if sys.version_info[0] == 3 and sys.version_info[1] >= 4:
        pass
    else:
        raise AnsibleFilterError("parse_genie: pyATS/Genie package requires python 3.4 or greater.")

    # Input validation

    # Is the CLI output a string?
    if not isinstance(cli_output, string_types):
        raise AnsibleError(
            "The content provided to the genie_parse filter was not a string."
        )

    # Is the command a string?
    if not isinstance(command, string_types):
        raise AnsibleFilterError(
            "The command provided to the genie_parse filter was not a string."
        )

    # Is the OS a string?
    if not isinstance(os, string_types):
        raise AnsibleFilterError(
            "The network OS provided to the genie_parse filter was not a string."
        )

    # Is the OS provided by the user a supported OS by Genie?
    # Supported Genie OSes: https://github.com/CiscoTestAutomation/genieparser/tree/master/src/genie/libs/parser
    supported_oses = ["ios", "iosxe", "iosxr", "junos", "nxos"]
    if os.lower() not in supported_oses:
        raise AnsibleFilterError(
            "The network OS provided ({0}) to the genie_parse filter is not a supported OS in Genie.".format(
                os
            )
        )

    # Boilerplate code to get the parser functional
    # tb = Testbed()
    device = Device("new_device", os=os)

    device.custom.setdefault("abstraction", {})["order"] = ["os"]
    device.cli = AttrDict({"execute": None})

    # User input checking of the command provided. Does the command have a Genie parser?
    try:
        get_parser(command, device)
    except Exception as e:
        raise AnsibleFilterError(
            "genie_parse: {0} - Available parsers: {1}".format(
                to_native(e), "https://pubhub.devnetcloud.com/media/pyats-packages/docs/genie/genie_libs/#/parsers"
            )
        )

    # Try to parse the output
    try:
        parsed_output = device.parse(command, output=cli_output)
        return parsed_output
    except Exception as e:
        raise AnsibleFilterError(
            "genie_parse: {0} - Failed to parse command output. Hint: Do not use abbreviated cli commands.".format(
                to_native(e)
            )
        )


class FilterModule(object):
    """ Cisco pyATS/Genie Parser Filter """

    def filters(self):
        return {
            # jinja2 overrides
            "parse_genie": parse_genie
        }
