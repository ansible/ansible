# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import re

from ansible.cli.adhoc import AdHocCLI


def test_ansible_version(capsys, mocker):
    adhoc_cli = AdHocCLI(args=['/bin/ansible', '--version'])
    with pytest.raises(SystemExit):
        adhoc_cli.run()
    version = capsys.readouterr()
    try:
        version_lines = version.out.splitlines()
    except AttributeError:
        # Python 2.6 does return a named tuple, so get the first item
        version_lines = version[0].splitlines()

    assert len(version_lines) == 6, 'Incorrect number of lines in "ansible --version" output'
    assert re.match('ansible [0-9.a-z]+$', version_lines[0]), 'Incorrect ansible version line in "ansible --version" output'
    assert re.match('  config file = .*$', version_lines[1]), 'Incorrect config file line in "ansible --version" output'
    assert re.match('  configured module search path = .*$', version_lines[2]), 'Incorrect module search path in "ansible --version" output'
    assert re.match('  ansible python module location = .*$', version_lines[3]), 'Incorrect python module location in "ansible --version" output'
    assert re.match('  executable location = .*$', version_lines[4]), 'Incorrect executable locaction in "ansible --version" output'
    assert re.match('  python version = .*$', version_lines[5]), 'Incorrect python version in "ansible --version" output'
