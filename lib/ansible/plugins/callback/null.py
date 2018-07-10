# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: 'null'
    callback_type: stdout
    requirements:
      - set as main display callback
    short_description: Don't display stuff to screen
    version_added: "2.5"
    description:
        - This callback prevents outputing events to screen
'''

from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):

    '''
    This callback wont print messages to stdout when new callback events are received.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'null'
