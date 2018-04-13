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

import os

from ansible import constants as C
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.module_utils._text import to_native, to_text
from ansible.playbook import Playbook
from ansible.template import Templar
from ansible.utils.helpers import pct_to_int
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.utils.path import makedirs_safe
from ansible.utils.ssh_functions import check_for_controlpersist

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class PlaybookExecutor:

    '''
    This is the primary class for executing playbooks, and thus the
    basis for bin/ansible-playbook operation.
    '''

    def __init__(self, playbooks, inventory, variable_manager, loader, options, passwords):
        self._playbooks = playbooks
        self._inventory = inventory
        self._variable_manager = variable_manager
        self._loader = loader
        self._options = options
        self.passwords = passwords
        self._unreachable_hosts = dict()

        if options.listhosts or options.listtasks or options.listtags or options.syntax:
            self._tqm = None
        else:
            self._tqm = TaskQueueManager(inventory=inventory, variable_manager=variable_manager, loader=loader, options=options, passwords=self.passwords)

        # Note: We run this here to cache whether the default ansible ssh
        # executable supports control persist.  Sometime in the future we may
        # need to enhance this to check that ansible_ssh_executable specified
        # in inventory is also cached.  We can't do this caching at the point
        # where it is used (in task_executor) because that is post-fork and
        # therefore would be discarded after every task.
        check_for_controlpersist(C.ANSIBLE_SSH_EXECUTABLE)

    def run(self):
        '''
        Run the given playbook, based on the settings in the play which
        may limit the runs to serialized groups, etc.
        '''

        result = 0
        entrylist = []
        entry = {}
        try:
            for playbook_path in self._playbooks:
                pb = Playbook.load(playbook_path, variable_manager=self._variable_manager, loader=self._loader)
                # FIXME: move out of inventory self._inventory.set_playbook_basedir(os.path.realpath(os.path.dirname(playbook_path)))

                if self._tqm is None:  # we are doing a listing
                    entry = {'playbook': playbook_path}
                    entry['plays'] = []
                else:
                    # make sure the tqm has callbacks loaded
                    self._tqm.load_callbacks()
                    self._tqm.send_callback('v2_playbook_on_start', pb)

                i = 1
                plays = pb.get_plays()
                display.vv(u'%d plays in %s' % (len(plays), to_text(playbook_path)))

                for play in plays:
                    if play._included_path is not None:
                        self._loader.set_basedir(play._included_path)
                    else:
                        self._loader.set_basedir(pb._basedir)

                    # clear any filters which may have been applied to the inventory
                    self._inventory.remove_restriction()

                    # Create a temporary copy of the play here, so we can run post_validate
                    # on it without the templating changes affecting the original object.
                    # Doing this before vars_prompt to allow for using variables in prompt.
                    all_vars = self._variable_manager.get_vars(play=play)
                    templar = Templar(loader=self._loader, variables=all_vars)
                    new_play = play.copy()
                    new_play.post_validate(templar)

                    if play.vars_prompt:
                        for var in new_play.vars_prompt:
                            vname = var['name']
                            prompt = var.get("prompt", vname)
                            default = var.get("default", None)
                            private = boolean(var.get("private", True))
                            confirm = boolean(var.get("confirm", False))
                            encrypt = var.get("encrypt", None)
                            salt_size = var.get("salt_size", None)
                            salt = var.get("salt", None)

                            if vname not in self._variable_manager.extra_vars:
                                if self._tqm:
                                    self._tqm.send_callback('v2_playbook_on_vars_prompt', vname, private, prompt, encrypt, confirm, salt_size, salt, default)
                                    play.vars[vname] = display.do_var_prompt(vname, private, prompt, encrypt, confirm, salt_size, salt, default)
                                else:  # we are either in --list-<option> or syntax check
                                    play.vars[vname] = default

                        # Post validating again in case variables were entered in the prompt.
                        all_vars = self._variable_manager.get_vars(play=play)
                        templar = Templar(loader=self._loader, variables=all_vars)
                        new_play.post_validate(templar)

                    if self._options.syntax:
                        continue

                    if self._tqm is None:
                        # we are just doing a listing
                        entry['plays'].append(new_play)

                    else:
                        self._tqm._unreachable_hosts.update(self._unreachable_hosts)

                        previously_failed = len(self._tqm._failed_hosts)
                        previously_unreachable = len(self._tqm._unreachable_hosts)

                        break_play = False
                        # we are actually running plays
                        batches = self._get_serialized_batches(new_play)
                        if len(batches) == 0:
                            self._tqm.send_callback('v2_playbook_on_play_start', new_play)
                            self._tqm.send_callback('v2_playbook_on_no_hosts_matched')
                        for batch in batches:
                            # restrict the inventory to the hosts in the serialized batch
                            self._inventory.restrict_to_hosts(batch)
                            # and run it...
                            result = self._tqm.run(play=play)

                            # break the play if the result equals the special return code
                            if result & self._tqm.RUN_FAILED_BREAK_PLAY != 0:
                                result = self._tqm.RUN_FAILED_HOSTS
                                break_play = True

                            # check the number of failures here, to see if they're above the maximum
                            # failure percentage allowed, or if any errors are fatal. If either of those
                            # conditions are met, we break out, otherwise we only break out if the entire
                            # batch failed
                            failed_hosts_count = len(self._tqm._failed_hosts) + len(self._tqm._unreachable_hosts) - \
                                (previously_failed + previously_unreachable)

                            if len(batch) == failed_hosts_count:
                                break_play = True
                                break

                            # update the previous counts so they don't accumulate incorrectly
                            # over multiple serial batches
                            previously_failed += len(self._tqm._failed_hosts) - previously_failed
                            previously_unreachable += len(self._tqm._unreachable_hosts) - previously_unreachable

                            # save the unreachable hosts from this batch
                            self._unreachable_hosts.update(self._tqm._unreachable_hosts)

                        if break_play:
                            break

                    i = i + 1  # per play

                if entry:
                    entrylist.append(entry)  # per playbook

                # send the stats callback for this playbook
                if self._tqm is not None:
                    if C.RETRY_FILES_ENABLED:
                        retries = set(self._tqm._failed_hosts.keys())
                        retries.update(self._tqm._unreachable_hosts.keys())
                        retries = sorted(retries)
                        if len(retries) > 0:
                            if C.RETRY_FILES_SAVE_PATH:
                                basedir = C.RETRY_FILES_SAVE_PATH
                            elif playbook_path:
                                basedir = os.path.dirname(os.path.abspath(playbook_path))
                            else:
                                basedir = '~/'

                            (retry_name, _) = os.path.splitext(os.path.basename(playbook_path))
                            filename = os.path.join(basedir, "%s.retry" % retry_name)
                            if self._generate_retry_inventory(filename, retries):
                                display.display("\tto retry, use: --limit @%s\n" % filename)

                    self._tqm.send_callback('v2_playbook_on_stats', self._tqm._stats)

                # if the last result wasn't zero, break out of the playbook file name loop
                if result != 0:
                    break

            if entrylist:
                return entrylist

        finally:
            if self._tqm is not None:
                self._tqm.cleanup()
            if self._loader:
                self._loader.cleanup_all_tmp_files()

        if self._options.syntax:
            display.display("No issues encountered")
            return result

        return result

    def _get_serialized_batches(self, play):
        '''
        Returns a list of hosts, subdivided into batches based on
        the serial size specified in the play.
        '''

        # make sure we have a unique list of hosts
        all_hosts = self._inventory.get_hosts(play.hosts)
        all_hosts_len = len(all_hosts)

        # the serial value can be listed as a scalar or a list of
        # scalars, so we make sure it's a list here
        serial_batch_list = play.serial
        if len(serial_batch_list) == 0:
            serial_batch_list = [-1]

        cur_item = 0
        serialized_batches = []

        while len(all_hosts) > 0:
            # get the serial value from current item in the list
            serial = pct_to_int(serial_batch_list[cur_item], all_hosts_len)

            # if the serial count was not specified or is invalid, default to
            # a list of all hosts, otherwise grab a chunk of the hosts equal
            # to the current serial item size
            if serial <= 0:
                serialized_batches.append(all_hosts)
                break
            else:
                play_hosts = []
                for x in range(serial):
                    if len(all_hosts) > 0:
                        play_hosts.append(all_hosts.pop(0))

                serialized_batches.append(play_hosts)

            # increment the current batch list item number, and if we've hit
            # the end keep using the last element until we've consumed all of
            # the hosts in the inventory
            cur_item += 1
            if cur_item > len(serial_batch_list) - 1:
                cur_item = len(serial_batch_list) - 1

        return serialized_batches

    def _generate_retry_inventory(self, retry_path, replay_hosts):
        '''
        Called when a playbook run fails. It generates an inventory which allows
        re-running on ONLY the failed hosts.  This may duplicate some variable
        information in group_vars/host_vars but that is ok, and expected.
        '''
        try:
            makedirs_safe(os.path.dirname(retry_path))
            with open(retry_path, 'w') as fd:
                for x in replay_hosts:
                    fd.write("%s\n" % x)
        except Exception as e:
            display.warning("Could not create retry file '%s'.\n\t%s" % (retry_path, to_native(e)))
            return False

        return True
