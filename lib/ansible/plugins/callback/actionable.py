# (c) 2015, Andrew Gaffney <andrew@agaffney.org>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: actionable
    type: stdout
    short_description: shows only items that need attention
    description:
      - Use this callback when you dont care about OK nor Skipped.
      - This callback suppresses any non Failed or Changed status.
    version_added: "2.1"
    deprecated:
        why: The 'default' callback plugin now supports this functionality
        removed_in: '2.11'
        alternative: "'default' callback plugin with 'display_skipped_hosts = no' and 'display_ok_hosts = no' options"
    extends_documentation_fragment:
      - default_callback
    requirements:
      - set as stdout callback in configuration
    # Override defaults from 'default' callback plugin
    options:
      display_skipped_hosts:
        name: Show skipped hosts
        description: "Toggle to control displaying skipped task/host results in a task"
        type: bool
        default: no
        env:
          - name: DISPLAY_SKIPPED_HOSTS
            deprecated:
              why: environment variables without "ANSIBLE_" prefix are deprecated
              version: "2.12"
              alternatives: the "ANSIBLE_DISPLAY_SKIPPED_HOSTS" environment variable
          - name: ANSIBLE_DISPLAY_SKIPPED_HOSTS
        ini:
          - key: display_skipped_hosts
            section: defaults
      display_ok_hosts:
        name: Show 'ok' hosts
        description: "Toggle to control displaying 'ok' task/host results in a task"
        type: bool
        default: no
        env:
          - name: ANSIBLE_DISPLAY_OK_HOSTS
        ini:
          - key: display_ok_hosts
            section: defaults
        version_added: '2.7'
'''

from ansible.plugins.callback.default import CallbackModule as CallbackModule_default


class CallbackModule(CallbackModule_default):

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'actionable'
