# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
#
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import getpass
import locale
import os
import signal
import sys

from ansible.compat.six import string_types

from ansible import constants as C
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.playbook import Playbook
from ansible.template import Templar

from ansible.utils.color import colorize, hostcolor
from ansible.utils.encrypt import do_encrypt
from ansible.utils.unicode import to_unicode

class PlaybookExecutor:

    '''
    This is the primary class for executing playbooks, and thus the
    basis for bin/ansible-playbook operation.
    '''

    def __init__(self, playbooks, inventory, variable_manager, loader, display, options, passwords):
        self._playbooks        = playbooks
        self._inventory        = inventory
        self._variable_manager = variable_manager
        self._loader           = loader
        self._display          = display
        self._options          = options
        self.passwords         = passwords
        self._unreachable_hosts = dict()

        if options.listhosts or options.listtasks or options.listtags or options.syntax:
            self._tqm = None
        else:
            self._tqm = TaskQueueManager(inventory=inventory, variable_manager=variable_manager, loader=loader, display=display, options=options, passwords=self.passwords)

    def run(self):

        '''
        Run the given playbook, based on the settings in the play which
        may limit the runs to serialized groups, etc.
        '''

        signal.signal(signal.SIGINT, self._cleanup)

        result = 0
        entrylist = []
        entry = {}
        try:
            for playbook_path in self._playbooks:
                pb = Playbook.load(playbook_path, variable_manager=self._variable_manager, loader=self._loader)
                self._inventory.set_playbook_basedir(os.path.dirname(playbook_path))

                if self._tqm is None: # we are doing a listing
                    entry = {'playbook': playbook_path}
                    entry['plays'] = []

                i = 1
                plays = pb.get_plays()
                self._display.vv('%d plays in %s' % (len(plays), playbook_path))

                for play in plays:
                    if play._included_path is not None:
                        self._loader.set_basedir(play._included_path)
                    else:
                        self._loader.set_basedir(pb._basedir)

                    # clear any filters which may have been applied to the inventory
                    self._inventory.remove_restriction()

                    if play.vars_prompt:
                        for var in play.vars_prompt:
                            vname     = var['name']
                            prompt    = var.get("prompt", vname)
                            default   = var.get("default", None)
                            private   = var.get("private", True)
                            confirm   = var.get("confirm", False)
                            encrypt   = var.get("encrypt", None)
                            salt_size = var.get("salt_size", None)
                            salt      = var.get("salt", None)

                            if vname not in play.vars:
                                if self._tqm:
                                    self._tqm.send_callback('v2_playbook_on_vars_prompt', vname, private, prompt, encrypt, confirm, salt_size, salt, default)
                                play.vars[vname] = self._do_var_prompt(vname, private, prompt, encrypt, confirm, salt_size, salt, default)

                    # Create a temporary copy of the play here, so we can run post_validate
                    # on it without the templating changes affecting the original object.
                    all_vars = self._variable_manager.get_vars(loader=self._loader, play=play)
                    templar = Templar(loader=self._loader, variables=all_vars)
                    new_play = play.copy()
                    new_play.post_validate(templar)

                    if self._options.syntax:
                        continue

                    if self._tqm is None:
                        # we are just doing a listing
                        entry['plays'].append(new_play)

                    else:
                        # make sure the tqm has callbacks loaded
                        self._tqm.load_callbacks()
                        self._tqm._unreachable_hosts.update(self._unreachable_hosts)

                        # we are actually running plays
                        for batch in self._get_serialized_batches(new_play):
                            if len(batch) == 0:
                                self._tqm.send_callback('v2_playbook_on_play_start', new_play)
                                self._tqm.send_callback('v2_playbook_on_no_hosts_matched')
                                break

                            # restrict the inventory to the hosts in the serialized batch
                            self._inventory.restrict_to_hosts(batch)
                            # and run it...
                            result = self._tqm.run(play=play)

                            # check the number of failures here, to see if they're above the maximum
                            # failure percentage allowed, or if any errors are fatal. If either of those
                            # conditions are met, we break out, otherwise we only break out if the entire
                            # batch failed
                            failed_hosts_count = len(self._tqm._failed_hosts) + len(self._tqm._unreachable_hosts)
                            if new_play.any_errors_fatal and failed_hosts_count > 0:
                                break
                            elif new_play.max_fail_percentage is not None and \
                               int((new_play.max_fail_percentage)/100.0 * len(batch)) > int((len(batch) - failed_hosts_count) / len(batch) * 100.0):
                                break
                            elif len(batch) == failed_hosts_count:
                                break

                            # clear the failed hosts dictionaires in the TQM for the next batch
                            self._unreachable_hosts.update(self._tqm._unreachable_hosts)
                            self._tqm.clear_failed_hosts()

                        # if the last result wasn't zero or 3 (some hosts were unreachable),
                        # break out of the serial batch loop
                        if result not in (0, 3):
                            break

                    i = i + 1 # per play

                if entry:
                    entrylist.append(entry) # per playbook

                # if the last result wasn't zero, break out of the playbook file name loop
                if result != 0:
                    break

            if entrylist:
                return entrylist

        finally:
            if self._tqm is not None:
                self._cleanup()

        if self._options.syntax:
            self.display.display("No issues encountered")
            return result

        # FIXME: this stat summary stuff should be cleaned up and moved
        #        to a new method, if it even belongs here...
        self._display.banner("PLAY RECAP")

        hosts = sorted(self._tqm._stats.processed.keys())
        for h in hosts:
            t = self._tqm._stats.summarize(h)

            self._display.display(u"%s : %s %s %s %s" % (
                hostcolor(h, t),
                colorize(u'ok', t['ok'], 'green'),
                colorize(u'changed', t['changed'], 'yellow'),
                colorize(u'unreachable', t['unreachable'], 'red'),
                colorize(u'failed', t['failures'], 'red')),
                screen_only=True
            )

            self._display.display(u"%s : %s %s %s %s" % (
                hostcolor(h, t, False),
                colorize(u'ok', t['ok'], None),
                colorize(u'changed', t['changed'], None),
                colorize(u'unreachable', t['unreachable'], None),
                colorize(u'failed', t['failures'], None)),
                log_only=True
            )

        self._display.display("", screen_only=True)
        # END STATS STUFF

        return result

    def _cleanup(self, signum=None, framenum=None):
        return self._tqm.cleanup()

    def _get_serialized_batches(self, play):
        '''
        Returns a list of hosts, subdivided into batches based on
        the serial size specified in the play.
        '''

        # make sure we have a unique list of hosts
        all_hosts = self._inventory.get_hosts(play.hosts)

        # check to see if the serial number was specified as a percentage,
        # and convert it to an integer value based on the number of hosts
        if isinstance(play.serial, string_types) and play.serial.endswith('%'):
            serial_pct = int(play.serial.replace("%",""))
            serial = int((serial_pct/100.0) * len(all_hosts))
        else:
            if play.serial is None: 
                serial = -1
            else:
                serial = int(play.serial)

        # if the serial count was not specified or is invalid, default to
        # a list of all hosts, otherwise split the list of hosts into chunks
        # which are based on the serial size
        if serial <= 0:
            return [all_hosts]
        else:
            serialized_batches = []

            while len(all_hosts) > 0:
                play_hosts = []
                for x in range(serial):
                    if len(all_hosts) > 0:
                        play_hosts.append(all_hosts.pop(0))

                serialized_batches.append(play_hosts)

            return serialized_batches

    def _do_var_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None):

        if sys.__stdin__.isatty():
            if prompt and default is not None:
                msg = "%s [%s]: " % (prompt, default)
            elif prompt:
                msg = "%s: " % prompt
            else:
                msg = 'input for %s: ' % varname

            def do_prompt(prompt, private):
                if sys.stdout.encoding:
                    msg = prompt.encode(sys.stdout.encoding)
                else:
                    # when piping the output, or at other times when stdout
                    # may not be the standard file descriptor, the stdout
                    # encoding may not be set, so default to something sane
                    msg = prompt.encode(locale.getpreferredencoding())
                if private:
                    return getpass.getpass(msg)
                return raw_input(msg)

            if confirm:
                while True:
                    result = do_prompt(msg, private)
                    second = do_prompt("confirm " + msg, private)
                    if result == second:
                        break
                    self._display.display("***** VALUES ENTERED DO NOT MATCH ****")
            else:
                result = do_prompt(msg, private)
        else:
            result = None
            self._display.warning("Not prompting as we are not in interactive mode")

        # if result is false and default is not None
        if not result and default is not None:
            result = default

        if encrypt:
            result = do_encrypt(result, encrypt, salt_size, salt)

        # handle utf-8 chars
        result = to_unicode(result, errors='strict')
        return result


