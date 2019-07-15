# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible.cli.adhoc import AdHocCLI


def test_simple_command():
    """ Test valid command and its run"""
    adhoc_cli = AdHocCLI(['/bin/ansible', '-m', 'command', 'localhost', '-a', 'echo "hi"'])
    adhoc_cli.parse()
    ret = adhoc_cli.run()
    assert ret == 0
