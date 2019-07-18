# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from ansible.cli.adhoc import AdHocCLI
from ansible.module_utils._text import to_bytes


def my_trace(frame, event, arg):
    tf = open('/tmp/trace.log', 'ab')
    # with tempfile.TemporaryFile() as tf:
    tf.write(b'%s %s %s' % (to_bytes(frame.f_code.co_filename), to_bytes(frame.f_lineno), to_bytes(event)))
    tf.write(b'In test_adhoc_simple_command.py\n')
    tf.close()


def test_simple_command():
    """ Test valid command and its run"""
    adhoc_cli = AdHocCLI(['/bin/ansible', '-m', 'command', 'localhost', '-a', 'echo "hi"'])
    adhoc_cli.parse()
    ret = adhoc_cli.run()
    assert ret == 0
