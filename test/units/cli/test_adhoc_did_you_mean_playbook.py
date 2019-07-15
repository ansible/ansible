# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible.cli.adhoc import AdHocCLI
from ansible.errors import AnsibleOptionsError


def test_did_you_mean_playbook():
    """ Test adhoc with yml file as argument parameter"""
    adhoc_cli = AdHocCLI(['/bin/ansible', '-m', 'command', 'localhost.yml'])
    adhoc_cli.parse()
    with pytest.raises(AnsibleOptionsError) as exec_info:
        adhoc_cli.run()
    assert 'No argument passed to command module (did you mean to run ansible-playbook?)' == str(exec_info.value)
