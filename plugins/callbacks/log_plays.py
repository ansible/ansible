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

import os
import time
import json

# NOTE: in Ansible 1.2 or later general logging is available without
# this plugin, just set ANSIBLE_LOG_PATH as an environment variable
# or log_path in the DEFAULTS section of your ansible configuration
# file.  This callback is an example of per hosts logging for those
# that want it.

TIME_FORMAT="%b %d %Y %H:%M:%S"
MSG_FORMAT="%(now)s - %(category)s - %(data)s\n\n"

if not os.path.exists("/var/log/ansible/hosts"):
    os.makedirs("/var/log/ansible/hosts")

def log(host, category, data):
    if type(data) == dict:
        if 'verbose_override' in data:
            # avoid logging extraneous data from facts
            data = 'omitted'
        else:
            data = data.copy()
            invocation = data.pop('invocation', None)
            data = json.dumps(data)
            if invocation is not None:
                data = json.dumps(invocation) + " => %s " % data

    path = os.path.join("/var/log/ansible/hosts", host)
    now = time.strftime(TIME_FORMAT, time.localtime())
    fd = open(path, "a")
    fd.write(MSG_FORMAT % dict(now=now, category=category, data=data))
    fd.close()

class CallbackModule(object):
    """
    logs playbook results, per host, in /var/log/ansible/hosts
    """

    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        log(host, 'FAILED', res)

    def runner_on_ok(self, host, res):
        log(host, 'OK', res)

    def runner_on_skipped(self, host, item=None):
        log(host, 'SKIPPED', '...')

    def runner_on_unreachable(self, host, res):
        log(host, 'UNREACHABLE', res)

    def runner_on_no_hosts(self):
        pass

    def runner_on_async_poll(self, host, res, jid, clock):
        pass

    def runner_on_async_ok(self, host, res, jid):
        pass

    def runner_on_async_failed(self, host, res, jid):
        log(host, 'ASYNC_FAILED', res)

    def playbook_on_start(self):
        pass

    def playbook_on_notify(self, host, handler):
        pass

    def playbook_on_no_hosts_matched(self):
        pass

    def playbook_on_no_hosts_remaining(self):
        pass

    def playbook_on_task_start(self, name, is_conditional):
        pass

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None):
        pass

    def playbook_on_setup(self):
        pass

    def playbook_on_import_for_host(self, host, imported_file):
        log(host, 'IMPORTED', imported_file)

    def playbook_on_not_import_for_host(self, host, missing_file):
        log(host, 'NOTIMPORTED', missing_file)

    def playbook_on_play_start(self, name):
        pass

    def playbook_on_stats(self, stats):
        pass

