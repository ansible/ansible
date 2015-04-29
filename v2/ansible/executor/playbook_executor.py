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

import signal

from ansible import constants as C
from ansible.errors import *
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.playbook import Playbook

from ansible.utils.color import colorize, hostcolor
from ansible.utils.debug import debug

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

        if options.listhosts or options.listtasks or options.listtags:
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

                if self._tqm is None: # we are doing a listing
                    entry = {'playbook': playbook_path}
                    entry['plays'] = []

                i = 1
                plays = pb.get_plays()
                self._display.vv('%d plays in %s' % (len(plays), playbook_path))

                for play in plays:
                    self._inventory.remove_restriction()

                    # Create a temporary copy of the play here, so we can run post_validate
                    # on it without the templating changes affecting the original object.
                    all_vars = self._variable_manager.get_vars(loader=self._loader, play=play)
                    new_play = play.copy()
                    new_play.post_validate(all_vars, fail_on_undefined=False)

                    if self._tqm is None:
                        # we are just doing a listing

                        pname =  new_play.get_name().strip()
                        if pname == 'PLAY: <no name specified>':
                            pname = 'PLAY: #%d' % i
                        p = { 'name': pname }

                        if self._options.listhosts:
                            p['pattern']=play.hosts
                            p['hosts']=set(self._inventory.get_hosts(new_play.hosts))

                        #TODO: play tasks are really blocks, need to figure out how to get task objects from them
                        elif self._options.listtasks:
                            p['tasks'] = []
                            for task in play.get_tasks():
                               p['tasks'].append(task)
                               #p['tasks'].append({'name': task.get_name().strip(), 'tags': task.tags})

                        elif self._options.listtags:
                            p['tags'] = set(new_play.tags)
                            for task in play.get_tasks():
                                p['tags'].update(task)
                                #p['tags'].update(task.tags)
                        entry['plays'].append(p)

                    else:
                        # we are actually running plays
                        for batch in self._get_serialized_batches(new_play):
                            if len(batch) == 0:
                                self._tqm.send_callback('v2_playbook_on_play_start', new_play)
                                self._tqm.send_callback('v2_playbook_on_no_hosts_matched')
                                result = 0
                                break
                            # restrict the inventory to the hosts in the serialized batch
                            self._inventory.restrict_to_hosts(batch)
                            # and run it...
                            result = self._tqm.run(play=play)
                            if result != 0:
                                break

                        if result != 0:
                            break

                    i = i + 1 # per play

                if entry:
                    entrylist.append(entry) # per playbook

            if entrylist:
                return entrylist

        finally:
            if self._tqm is not None:
                self._cleanup()

        # FIXME: this stat summary stuff should be cleaned up and moved
        #        to a new method, if it even belongs here...
        self._display.banner("PLAY RECAP")

        hosts = sorted(self._tqm._stats.processed.keys())
        for h in hosts:
            t = self._tqm._stats.summarize(h)

            self._display.display("%s : %s %s %s %s" % (
                hostcolor(h, t),
                colorize('ok', t['ok'], 'green'),
                colorize('changed', t['changed'], 'yellow'),
                colorize('unreachable', t['unreachable'], 'red'),
                colorize('failed', t['failures'], 'red')),
                screen_only=True
            )

            self._display.display("%s : %s %s %s %s" % (
                hostcolor(h, t, False),
                colorize('ok', t['ok'], None),
                colorize('changed', t['changed'], None),
                colorize('unreachable', t['unreachable'], None),
                colorize('failed', t['failures'], None)),
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
        if isinstance(play.serial, basestring) and play.serial.endswith('%'):
            serial_pct = int(play.serial.replace("%",""))
            serial = int((serial_pct/100.0) * len(all_hosts))
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
