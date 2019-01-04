# Copyright: (c) 2019, Ansible Project
# Copyright: (c) 2019, Abhijeet Kasurde <akasurde@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: espeak
    type: notification
    requirements:
      - whitelisting in configuration
      - the espeak command line program
    short_description: one line Ansible screen output
    version_added: '2.8'
    options:
      espeak_bin:
        description: Espeak binary location
        env:
          - name: ESPEAK_BIN
        required: True
        default: /usr/local/bin/espeak
        ini:
          - section: callback_espeak
            key: espeak_bin
      espeak_voice:
        description: Espeak voice name
        env:
          - name: ESPEAK_VOICE
        required: False
        default: default
        ini:
          - section: callback_espeak
            key: espeak_voice
    description:
      - This plugin will use the 'espeak' program to "speak" about play events.
'''

import subprocess
import os
from ansible.module_utils.six.moves import shlex_quote
from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    """
    Make Ansible speak to you
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'espeak'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.espeak_bin = None

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        self.espeak_bin = self.get_option('espeak_bin')
        self.voice = self.get_option('espeak_voice')

        # plugin disable itself if espeak is not present
        if not os.path.exists(self.espeak_bin):
            self.disabled = True
            self._display.warning("%s does not exist, plugin %s disabled" % (self.espeak_bin, self.CALLBACK_NAME))

    def speak(self, msg):
        subprocess.call([self.espeak_bin, shlex_quote(msg), '-v', shlex_quote(self.voice)])

    def runner_on_failed(self, host, res, ignore_errors=False):
        self.speak("Failure on host %s" % host)

    def runner_on_ok(self, host, res):
        self.speak("pew")

    def runner_on_skipped(self, host, item=None):
        self.speak("pew")

    def runner_on_unreachable(self, host, res):
        self.speak("Failure on host %s" % host)

    def runner_on_async_ok(self, host, res, jid):
        self.speak("pew")

    def runner_on_async_failed(self, host, res, jid):
        self.speak("Failure on host %s" % host)

    def playbook_on_start(self):
        self.speak("Running Playbook")

    def playbook_on_notify(self, host, handler):
        self.speak("pew")

    def playbook_on_task_start(self, name, is_conditional):
        if not is_conditional:
            self.speak("Starting task: %s" % name)
        else:
            self.speak("Notifying task: %s" % name)

    def playbook_on_setup(self):
        self.speak("Gathering facts")

    def playbook_on_play_start(self, name):
        self.speak("Starting play: %s" % name)

    def playbook_on_stats(self, stats):
        self.speak("Play complete")
