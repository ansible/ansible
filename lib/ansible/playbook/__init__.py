# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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

import ansible.inventory
import ansible.runner
import ansible.constants as C
from ansible import utils
from ansible import errors
import os
import collections
from play import Play

SETUP_CACHE = collections.defaultdict(dict)

class PlayBook(object):
    '''
    runs an ansible playbook, given as a datastructure or YAML filename.
    A playbook is a deployment, config management, or automation based
    set of commands to run in series.

    multiple plays/tasks do not execute simultaneously, but tasks in each
    pattern do execute in parallel (according to the number of forks
    requested) among the hosts they address
    '''

    # *****************************************************

    def __init__(self,
        playbook         = None,
        host_list        = C.DEFAULT_HOST_LIST,
        module_path      = C.DEFAULT_MODULE_PATH,
        forks            = C.DEFAULT_FORKS,
        timeout          = C.DEFAULT_TIMEOUT,
        remote_user      = C.DEFAULT_REMOTE_USER,
        remote_pass      = C.DEFAULT_REMOTE_PASS,
        sudo_pass        = C.DEFAULT_SUDO_PASS,
        remote_port      = C.DEFAULT_REMOTE_PORT,
        transport        = C.DEFAULT_TRANSPORT,
        private_key_file = C.DEFAULT_PRIVATE_KEY_FILE,
        callbacks        = None,
        runner_callbacks = None,
        stats            = None,
        sudo             = False,
        sudo_user        = C.DEFAULT_SUDO_USER,
        extra_vars       = None,
        only_tags        = None,
        subset           = C.DEFAULT_SUBSET):

        """
        playbook:         path to a playbook file
        host_list:        path to a file like /etc/ansible/hosts
        module_path:      path to ansible modules, like /usr/share/ansible/
        forks:            desired level of paralellism
        timeout:          connection timeout
        remote_user:      run as this user if not specified in a particular play
        remote_pass:      use this remote password (for all plays) vs using SSH keys
        sudo_pass:        if sudo==True, and a password is required, this is the sudo password
        remote_port:      default remote port to use if not specified with the host or play
        transport:        how to connect to hosts that don't specify a transport (local, paramiko, etc)
        callbacks         output callbacks for the playbook
        runner_callbacks: more callbacks, this time for the runner API
        stats:            holds aggregrate data about events occuring to each host
        sudo:             if not specified per play, requests all plays use sudo mode
        """

        self.SETUP_CACHE = SETUP_CACHE

        if playbook is None or callbacks is None or runner_callbacks is None or stats is None:
            raise Exception('missing required arguments')

        if extra_vars is None:
            extra_vars = {}
        if only_tags is None:
            only_tags = [ 'all' ]

        self.module_path      = module_path
        self.forks            = forks
        self.timeout          = timeout
        self.remote_user      = remote_user
        self.remote_pass      = remote_pass
        self.remote_port      = remote_port
        self.transport        = transport
        self.callbacks        = callbacks
        self.runner_callbacks = runner_callbacks
        self.stats            = stats
        self.sudo             = sudo
        self.sudo_pass        = sudo_pass
        self.sudo_user        = sudo_user
        self.extra_vars       = extra_vars
        self.global_vars      = {}
        self.private_key_file = private_key_file
        self.only_tags        = only_tags

        self.inventory        = ansible.inventory.Inventory(host_list)
        self.inventory.subset(subset)

        if not self.inventory._is_script:
            self.global_vars.update(self.inventory.get_group_variables('all'))

        self.basedir     = os.path.dirname(playbook)
        (self.playbook, self.play_basedirs) = self._load_playbook_from_file(playbook)
        self.module_path = self.module_path + os.pathsep + os.path.join(self.basedir, "library")

    # *****************************************************

    def _load_playbook_from_file(self, path):
        '''
        run top level error checking on playbooks and allow them to include other playbooks.
        '''

        playbook_data  = utils.parse_yaml_from_file(path)
        accumulated_plays = []
        play_basedirs = []

        if type(playbook_data) != list:
            raise errors.AnsibleError("parse error: playbooks must be formatted as a YAML list")

        for play in playbook_data:
            if type(play) != dict:
                raise errors.AnsibleError("parse error: each play in a playbook must a YAML dictionary (hash), recieved: %s" % play)
            if 'include' in play:
                if len(play.keys()) == 1:
                    included_path = utils.path_dwim(self.basedir, play['include'])
                    (plays, basedirs) = self._load_playbook_from_file(included_path)
                    accumulated_plays.extend(plays)
                    play_basedirs.extend(basedirs)

                else:
                    raise errors.AnsibleError("parse error: top level includes cannot be used with other directives: %s" % play)
            else:
                accumulated_plays.append(play)
                play_basedirs.append(os.path.dirname(path))

        return (accumulated_plays, play_basedirs)

    # *****************************************************

    def run(self):
        ''' run all patterns in the playbook '''
        plays = []
        matched_tags_all = set()
        unmatched_tags_all = set()

        # loop through all patterns and run them
        self.callbacks.on_start()
        for (play_ds, play_basedir) in zip(self.playbook, self.play_basedirs):
            play = Play(self, play_ds, play_basedir)
            matched_tags, unmatched_tags = play.compare_tags(self.only_tags)
            matched_tags_all = matched_tags_all | matched_tags
            unmatched_tags_all = unmatched_tags_all | unmatched_tags

            # if we have matched_tags, the play must be run.
            # if the play contains no tasks, assume we just want to gather facts
            if (len(matched_tags) > 0 or len(play.tasks()) == 0):
                plays.append(play)

        # if the playbook is invoked with --tags that don't exist at all in the playbooks
        # then we need to raise an error so that the user can correct the arguments.
        unknown_tags = set(self.only_tags) - (matched_tags_all | unmatched_tags_all)
        unknown_tags.discard('all')

        if len(unknown_tags) > 0:
            unmatched_tags_all.discard('all')
            msg = 'tag(s) not found in playbook: %s.  possible values: %s'
            unknown = ','.join(sorted(unknown_tags))
            unmatched = ','.join(sorted(unmatched_tags_all))
            raise errors.AnsibleError(msg % (unknown, unmatched))

        for play in plays:
            self._run_play(play)

        # summarize the results
        results = {}
        for host in self.stats.processed.keys():
            results[host] = self.stats.summarize(host)
        return results

    # *****************************************************

    def _async_poll(self, poller, async_seconds, async_poll_interval):
        ''' launch an async job, if poll_interval is set, wait for completion '''

        results = poller.wait(async_seconds, async_poll_interval)

        # mark any hosts that are still listed as started as failed
        # since these likely got killed by async_wrapper
        for host in poller.hosts_to_poll:
            reason = { 'failed' : 1, 'rc' : None, 'msg' : 'timed out' }
            self.runner_callbacks.on_failed(host, reason)
            results['contacted'][host] = reason

        return results

    # *****************************************************

    def _run_task_internal(self, task):
        ''' run a particular module step in a playbook '''

        hosts = [ h for h in self.inventory.list_hosts() if (h not in self.stats.failures) and (h not in self.stats.dark)]
        self.inventory.restrict_to(hosts)

        runner = ansible.runner.Runner(
            pattern=task.play.hosts, inventory=self.inventory, module_name=task.module_name,
            module_args=task.module_args, forks=self.forks,
            remote_pass=self.remote_pass, module_path=self.module_path,
            timeout=self.timeout, remote_user=task.play.remote_user,
            remote_port=task.play.remote_port, module_vars=task.module_vars,
            private_key_file=self.private_key_file,
            setup_cache=self.SETUP_CACHE, basedir=task.play.basedir,
            conditional=task.only_if, callbacks=self.runner_callbacks,
            sudo=task.play.sudo, sudo_user=task.play.sudo_user,
            transport=task.play.transport, sudo_pass=self.sudo_pass, is_playbook=True
        )

        if not task.task_type == 'action':
            try:
                action = __import__("ansible.playbook.%s" % task.task_type, fromlist=[task.task_type])
                action_class = getattr(action, task.task_type)
                results = runner.run_other_action(action_class)
            except ImportError:
                raise errors.AnsibleError("unable to locate and load %s" % task.task_type)
        elif task.async_seconds == 0:
            results = runner.run()
        else:
            results, poller = runner.run_async(task.async_seconds)
            self.stats.compute(results)
            if task.async_poll_interval > 0:
                # if not polling, playbook requested fire and forget, so don't poll
                results = self._async_poll(poller, task.async_seconds, task.async_poll_interval)

        self.inventory.lift_restriction()
        return results

    # *****************************************************

    def _run_task(self, play, task, is_handler):
        ''' run a single task in the playbook and recursively run any subtasks.  '''

        self.callbacks.on_task_start(task.name, is_handler)

        # load up an appropriate ansible runner to run the task in parallel
        results = self._run_task_internal(task)
        # if no hosts are matched, carry on
        if results is None:
            results = {}

        self.stats.compute(results, ignore_errors=task.ignore_errors)

        # add facts to the global setup cache
        for host, result in results['contacted'].iteritems():
            facts = result.get('ansible_facts', {})
            self.SETUP_CACHE[host].update(facts)
            if task.register:
                self.SETUP_CACHE[host][task.register] = result

        # flag which notify handlers need to be run
        if len(task.notify) > 0:
            for host, results in results.get('contacted',{}).iteritems():
                if results.get('changed', False):
                    for handler_name in task.notify:
                        self._flag_handler(play.handlers(), utils.template(handler_name, task.module_vars), host)

    # *****************************************************

    def _flag_handler(self, handlers, handler_name, host):
        '''
        if a task has any notify elements, flag handlers for run
        at end of execution cycle for hosts that have indicated
        changes have been made
        '''

        found = False
        for x in handlers:
            if handler_name == x.name:
                found = True
                self.callbacks.on_notify(host, x.name)
                x.notified_by.append(host)
        if not found:
            raise errors.AnsibleError("change handler (%s) is not defined" % handler_name)

    # *****************************************************

    def _do_setup_step(self, play):
        ''' get facts from the remote system '''

        host_list = [ h for h in self.inventory.list_hosts(play.hosts)
            if not (h in self.stats.failures or h in self.stats.dark) ]

        if not play.gather_facts:
            return {}

        self.callbacks.on_setup()
        self.inventory.restrict_to(host_list)

        # push any variables down to the system
        setup_results = ansible.runner.Runner(
            pattern=play.hosts, module_name='setup', module_args={}, inventory=self.inventory,
            forks=self.forks, module_path=self.module_path, timeout=self.timeout, remote_user=play.remote_user,
            remote_pass=self.remote_pass, remote_port=play.remote_port, private_key_file=self.private_key_file,
            setup_cache=self.SETUP_CACHE, callbacks=self.runner_callbacks, sudo=play.sudo, sudo_user=play.sudo_user,
            transport=play.transport, sudo_pass=self.sudo_pass, is_playbook=True
        ).run()
        self.stats.compute(setup_results, setup=True)

        self.inventory.lift_restriction()

        # now for each result, load into the setup cache so we can
        # let runner template out future commands
        setup_ok = setup_results.get('contacted', {})
        for (host, result) in setup_ok.iteritems():
            self.SETUP_CACHE[host] = result.get('ansible_facts', {})
        return setup_results

    # *****************************************************

    def _run_play(self, play):
        ''' run a list of tasks for a given pattern, in order '''

        self.callbacks.on_play_start(play.name)

        # get facts from system
        self._do_setup_step(play)

        # now with that data, handle contentional variable file imports!

        all_hosts = self.inventory.list_hosts(play.hosts)
        play.update_vars_files(all_hosts)

        serialized_batch = []
        if play.serial <= 0:
            serialized_batch = [all_hosts]
        else:
            # do N forks all the way through before moving to next
            while len(all_hosts) > 0:
                play_hosts = []
                for x in range(play.serial):
                    if len(all_hosts) > 0:
                        play_hosts.append(all_hosts.pop())
                serialized_batch.append(play_hosts)

        for on_hosts in serialized_batch:

            self.inventory.also_restrict_to(on_hosts)

            for task in play.tasks():
                # only run the task if the requested tags match
                should_run = False
                for x in self.only_tags:
                    for y in task.tags:
                        if (x==y):
                            should_run = True
                            break
                if should_run:
                    self._run_task(play, task, False)

            # run notify actions
            for handler in play.handlers():
                if len(handler.notified_by) > 0:
                    self.inventory.restrict_to(handler.notified_by)
                    self._run_task(play, handler, True)
                    self.inventory.lift_restriction()

            self.inventory.lift_also_restriction()
