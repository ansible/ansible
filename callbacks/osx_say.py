
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

FAILED_VOICE="Zarvox"
REGULAR_VOICE="Trinoids"
HAPPY_VOICE="Cellos"

def say(msg, voice):
    subprocess.call(["/usr/bin/say", msg, "--voice=%s" % (voice)])

class CallbackModule(object):

    """
    this is an example ansible callback file that does nothing.  You can drop
    other classes in the same directory to define your own handlers.  Methods
    you do not use can be omitted.

    example uses include: logging, emailing, storing info, etc
    """

    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        say("Failure on host %s" % host, FAILED_VOICE)

    def runner_on_ok(self, host, res):
        say("pew", "Princess")

    def runner_on_error(self, host, msg):
        pass

    def runner_on_skipped(self, host, item=None):
        say("pew", "Princess")

    def runner_on_unreachable(self, host, res):
        say("Failure on host %s" % host, FAILED_VOICE)

    def runner_on_no_hosts(self):
        pass

    def runner_on_async_poll(self, host, res, jid, clock):
        pass

    def runner_on_async_ok(self, host, res, jid):
        say("pew", "Princess")

    def runner_on_async_failed(self, host, res, jid):
        say("Failure on host %s" % host, FAILED_VOICE)

    def playbook_on_start(self):
        say("Running Playbook", REGULAR_VOICE)

    def playbook_on_notify(self, host, handler):
        say("pew", "Princess")

    def playbook_on_task_start(self, name, is_conditional):
        say("Starting task: %s" % name, REGULAR_VOICE)

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None):
        pass

    def playbook_on_setup(self):
        say("Gathering facts", REGULAR_VOICE)

    def playbook_on_import_for_host(self, host, imported_file):
        pass

    def playbook_on_not_import_for_host(self, host, missing_file):
        pass

    def playbook_on_play_start(self, pattern):
        say("Starting play: %s" % pattern, HAPPY_VOICE)

    def playbook_on_stats(self, stats):
        say("Play complete", HAPPY_VOICE)

