
# (C) 2012, Michael DeHaan, <michael.dehaan@gmail.com>

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

import subprocess
import os

FAILED_VOICE="Zarvox"
REGULAR_VOICE="Trinoids"
HAPPY_VOICE="Cellos"
LASER_VOICE="Princess"
SAY_CMD="/usr/bin/say"

def say(msg, voice):
    subprocess.call([SAY_CMD, msg, "--voice=%s" % (voice)])

class CallbackModule(object):
    """
    makes Ansible much more exciting on OS X.
    """
    def __init__(self):
        # plugin disable itself if say is not present
        # ansible will not call any callback if disabled is set to True
        if not os.path.exists(SAY_CMD):
            self.disabled = True
            print "%s does not exist, plugin %s disabled" % \
                    (SAY_CMD, os.path.basename(__file__))

    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        say("Failure on host %s" % host, FAILED_VOICE)

    def runner_on_ok(self, host, res):
        say("pew", LASER_VOICE)

    def runner_on_skipped(self, host, item=None):
        say("pew", LASER_VOICE)

    def runner_on_unreachable(self, host, res):
        say("Failure on host %s" % host, FAILED_VOICE)

    def runner_on_no_hosts(self):
        pass

    def runner_on_async_poll(self, host, res, jid, clock):
        pass

    def runner_on_async_ok(self, host, res, jid):
        say("pew", LASER_VOICE)

    def runner_on_async_failed(self, host, res, jid):
        say("Failure on host %s" % host, FAILED_VOICE)

    def playbook_on_start(self):
        say("Running Playbook", REGULAR_VOICE)

    def playbook_on_notify(self, host, handler):
        say("pew", LASER_VOICE)

    def playbook_on_no_hosts_matched(self):
        pass

    def playbook_on_no_hosts_remaining(self):
        pass

    def playbook_on_task_start(self, name, is_conditional):
        if not is_conditional:
            say("Starting task: %s" % name, REGULAR_VOICE)
        else:
            say("Notifying task: %s" % name, REGULAR_VOICE)

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None):
        pass

    def playbook_on_setup(self):
        say("Gathering facts", REGULAR_VOICE)

    def playbook_on_import_for_host(self, host, imported_file):
        pass

    def playbook_on_not_import_for_host(self, host, missing_file):
        pass

    def playbook_on_play_start(self, name):
        say("Starting play: %s" % name, HAPPY_VOICE)

    def playbook_on_stats(self, stats):
        say("Play complete", HAPPY_VOICE)

