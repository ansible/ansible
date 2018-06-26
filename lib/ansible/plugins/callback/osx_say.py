# (c) 2012, Michael DeHaan, <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: osx_say
    type: notification
    requirements:
      - whitelising in configuration
      - the '/usr/bin/say' command line program (standard on macOS)
    short_description: oneline Ansible screen output
    version_added: historical
    description:
      - This plugin will use the 'say' program to "speak" about play events.
'''

import subprocess
import os

from ansible.plugins.callback import CallbackBase

FAILED_VOICE = "Zarvox"
REGULAR_VOICE = "Trinoids"
HAPPY_VOICE = "Cellos"
LASER_VOICE = "Princess"
SAY_CMD = "/usr/bin/say"


class CallbackModule(CallbackBase):
    """
    makes Ansible much more exciting on macOS.
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'osx_say'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):

        super(CallbackModule, self).__init__()

        # plugin disable itself if say is not present
        # ansible will not call any callback if disabled is set to True
        if not os.path.exists(SAY_CMD):
            self.disabled = True
            self._display.warning("%s does not exist, plugin %s disabled" % (SAY_CMD, os.path.basename(__file__)))

    def say(self, msg, voice):
        subprocess.call([SAY_CMD, msg, "--voice=%s" % (voice)])

    def runner_on_failed(self, host, res, ignore_errors=False):
        self.say("Failure on host %s" % host, FAILED_VOICE)

    def runner_on_ok(self, host, res):
        self.say("pew", LASER_VOICE)

    def runner_on_skipped(self, host, item=None):
        self.say("pew", LASER_VOICE)

    def runner_on_unreachable(self, host, res):
        self.say("Failure on host %s" % host, FAILED_VOICE)

    def runner_on_async_ok(self, host, res, jid):
        self.say("pew", LASER_VOICE)

    def runner_on_async_failed(self, host, res, jid):
        self.say("Failure on host %s" % host, FAILED_VOICE)

    def playbook_on_start(self):
        self.say("Running Playbook", REGULAR_VOICE)

    def playbook_on_notify(self, host, handler):
        self.say("pew", LASER_VOICE)

    def playbook_on_task_start(self, name, is_conditional):
        if not is_conditional:
            self.say("Starting task: %s" % name, REGULAR_VOICE)
        else:
            self.say("Notifying task: %s" % name, REGULAR_VOICE)

    def playbook_on_setup(self):
        self.say("Gathering facts", REGULAR_VOICE)

    def playbook_on_play_start(self, name):
        self.say("Starting play: %s" % name, HAPPY_VOICE)

    def playbook_on_stats(self, stats):
        self.say("Play complete", HAPPY_VOICE)
