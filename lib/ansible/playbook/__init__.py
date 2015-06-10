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

import ansible.inventory
import ansible.constants as C
import ansible.runner
from ansible.utils.template import template
from ansible import utils
from ansible import errors
from ansible.module_utils.splitter import split_args, unquote
import ansible.callbacks
import ansible.cache
import os
import shlex
import collections
from play import Play
import StringIO
import pipes

# the setup cache stores all variables about a host
# gathered during the setup step, while the vars cache
# holds all other variables about a host
SETUP_CACHE = ansible.cache.FactCache()
VARS_CACHE  = collections.defaultdict(dict)
RESERVED_TAGS = ['all','tagged','untagged','always']


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
        module_path      = None,
        forks            = C.DEFAULT_FORKS,
        timeout          = C.DEFAULT_TIMEOUT,
        remote_user      = C.DEFAULT_REMOTE_USER,
        remote_pass      = C.DEFAULT_REMOTE_PASS,
        remote_port      = None,
        transport        = C.DEFAULT_TRANSPORT,
        private_key_file = C.DEFAULT_PRIVATE_KEY_FILE,
        callbacks        = None,
        runner_callbacks = None,
        stats            = None,
        extra_vars       = None,
        only_tags        = None,
        skip_tags        = None,
        subset           = C.DEFAULT_SUBSET,
        inventory        = None,
        check            = False,
        diff             = False,
        any_errors_fatal = False,
        vault_password   = False,
        force_handlers   = False,
        # privelege escalation
        become           = C.DEFAULT_BECOME,
        become_method    = C.DEFAULT_BECOME_METHOD,
        become_user      = C.DEFAULT_BECOME_USER,
        become_pass      = None,
    ):

        """
        playbook:         path to a playbook file
        host_list:        path to a file like /etc/ansible/hosts
        module_path:      path to ansible modules, like /usr/share/ansible/
        forks:            desired level of parallelism
        timeout:          connection timeout
        remote_user:      run as this user if not specified in a particular play
        remote_pass:      use this remote password (for all plays) vs using SSH keys
        remote_port:      default remote port to use if not specified with the host or play
        transport:        how to connect to hosts that don't specify a transport (local, paramiko, etc)
        callbacks         output callbacks for the playbook
        runner_callbacks: more callbacks, this time for the runner API
        stats:            holds aggregrate data about events occurring to each host
        inventory:        can be specified instead of host_list to use a pre-existing inventory object
        check:            don't change anything, just try to detect some potential changes
        any_errors_fatal: terminate the entire execution immediately when one of the hosts has failed
        force_handlers:   continue to notify and run handlers even if a task fails
        """

        self.SETUP_CACHE = SETUP_CACHE
        self.VARS_CACHE  = VARS_CACHE

        arguments = []
        if playbook is None:
            arguments.append('playbook')
        if callbacks is None:
            arguments.append('callbacks')
        if runner_callbacks is None:
            arguments.append('runner_callbacks')
        if stats is None:
            arguments.append('stats')
        if arguments:
            raise Exception('PlayBook missing required arguments: %s' % ', '.join(arguments))

        if extra_vars is None:
            extra_vars = {}
        if only_tags is None:
            only_tags = [ 'all' ]
        if skip_tags is None:
            skip_tags = []

        self.check            = check
        self.diff             = diff
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
        self.extra_vars       = extra_vars
        self.global_vars      = {}
        self.private_key_file = private_key_file
        self.only_tags        = only_tags
        self.skip_tags        = skip_tags
        self.any_errors_fatal = any_errors_fatal
        self.vault_password   = vault_password
        self.force_handlers   = force_handlers

        self.become           = become
        self.become_method    = become_method
        self.become_user      = become_user
        self.become_pass      = become_pass

        self.callbacks.playbook = self
        self.runner_callbacks.playbook = self

        if inventory is None:
            self.inventory    = ansible.inventory.Inventory(host_list)
            self.inventory.subset(subset)
        else:
            self.inventory    = inventory

        if self.module_path is not None:
            utils.plugins.module_finder.add_directory(self.module_path)

        self.basedir     = os.path.dirname(playbook) or '.'
        utils.plugins.push_basedir(self.basedir)

        # let inventory know the playbook basedir so it can load more vars
        self.inventory.set_playbook_basedir(self.basedir)

        vars = extra_vars.copy()
        vars['playbook_dir'] = os.path.abspath(self.basedir)
        if self.inventory.basedir() is not None:
            vars['inventory_dir'] = self.inventory.basedir()

        if self.inventory.src() is not None:
            vars['inventory_file'] = self.inventory.src()

        self.filename = playbook
        (self.playbook, self.play_basedirs) = self._load_playbook_from_file(playbook, vars)
        ansible.callbacks.load_callback_plugins()
        ansible.callbacks.set_playbook(self.callbacks, self)

        self._ansible_version = utils.version_info(gitinfo=True)

    # *****************************************************

    def _get_playbook_vars(self, play_ds, existing_vars):
        '''
        Gets the vars specified with the play and blends them
        with any existing vars that have already been read in
        '''
        new_vars = existing_vars.copy()
        if 'vars' in play_ds:
            if isinstance(play_ds['vars'], dict):
                new_vars.update(play_ds['vars'])
            elif isinstance(play_ds['vars'], list):
                for v in play_ds['vars']:
                    new_vars.update(v)
        return new_vars

    # *****************************************************

    def _get_include_info(self, play_ds, basedir, existing_vars={}):
        '''
        Gets any key=value pairs specified with the included file
        name and returns the merged vars along with the path
        '''
        new_vars = existing_vars.copy()
        tokens = split_args(play_ds.get('include', ''))
        for t in tokens[1:]:
            try:
                (k,v) = unquote(t).split("=", 1)
                new_vars[k] = template(basedir, v, new_vars)
            except ValueError, e:
                raise errors.AnsibleError('included playbook variables must be in the form k=v, got: %s' % t)

        return (new_vars, unquote(tokens[0]))

    # *****************************************************

    def _get_playbook_vars_files(self, play_ds, existing_vars_files):
        new_vars_files = list(existing_vars_files)
        if 'vars_files' in play_ds:
            new_vars_files = utils.list_union(new_vars_files, play_ds['vars_files'])
        return new_vars_files

    # *****************************************************

    def _extend_play_vars(self, play, vars={}):
        '''
        Extends the given play's variables with the additional specified vars.
        '''

        if 'vars' not in play or not play['vars']:
            # someone left out or put an empty "vars:" entry in their playbook
            return vars.copy()

        play_vars = None
        if isinstance(play['vars'], dict):
            play_vars = play['vars'].copy()
            play_vars.update(vars)
        elif isinstance(play['vars'], list):
            # nobody should really do this, but handle vars: a=1 b=2
            play_vars = play['vars'][:]
            play_vars.extend([{k:v} for k,v in vars.iteritems()])

        return play_vars

    # *****************************************************

    def _load_playbook_from_file(self, path, vars={}, vars_files=[]):
        '''
        run top level error checking on playbooks and allow them to include other playbooks.
        '''

        playbook_data = utils.parse_yaml_from_file(path, vault_password=self.vault_password)
        accumulated_plays = []
        play_basedirs = []

        if type(playbook_data) != list:
            raise errors.AnsibleError("parse error: playbooks must be formatted as a YAML list, got %s" % type(playbook_data))

        basedir = os.path.dirname(path) or '.'
        utils.plugins.push_basedir(basedir)
        for play in playbook_data:
            if type(play) != dict:
                raise errors.AnsibleError("parse error: each play in a playbook must be a YAML dictionary (hash), received: %s" % play)

            if 'include' in play:
                # a playbook (list of plays) decided to include some other list of plays
                # from another file.  The result is a flat list of plays in the end.

                play_vars = self._get_playbook_vars(play, vars)
                play_vars_files = self._get_playbook_vars_files(play, vars_files)
                inc_vars, inc_path = self._get_include_info(play, basedir, play_vars)
                play_vars.update(inc_vars)

                included_path = utils.path_dwim(basedir, template(basedir, inc_path, play_vars))
                (plays, basedirs) = self._load_playbook_from_file(included_path, vars=play_vars, vars_files=play_vars_files)
                for p in plays:
                    # support for parameterized play includes works by passing
                    # those variables along to the subservient play
                    p['vars'] = self._extend_play_vars(p, play_vars)
                    # now add in the vars_files
                    p['vars_files'] = utils.list_union(p.get('vars_files', []), play_vars_files)

                accumulated_plays.extend(plays)
                play_basedirs.extend(basedirs)

            else:

                # this is a normal (non-included play)
                accumulated_plays.append(play)
                play_basedirs.append(basedir)

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
            play = Play(self, play_ds, play_basedir, vault_password=self.vault_password)
            assert play is not None

            matched_tags, unmatched_tags = play.compare_tags(self.only_tags)

            matched_tags_all = matched_tags_all | matched_tags
            unmatched_tags_all = unmatched_tags_all | unmatched_tags

            # Remove tasks we wish to skip
            matched_tags = matched_tags - set(self.skip_tags)

            # if we have matched_tags, the play must be run.
            # if the play contains no tasks, assume we just want to gather facts
            # in this case there are actually 3 meta tasks (handler flushes) not 0
            # tasks, so that's why there's a check against 3
            if (len(matched_tags) > 0 or len(play.tasks()) == 3):
                plays.append(play)

        # if the playbook is invoked with --tags or --skip-tags that don't
        # exist at all in the playbooks then we need to raise an error so that
        # the user can correct the arguments.
        unknown_tags = ((set(self.only_tags) | set(self.skip_tags)) -
                        (matched_tags_all | unmatched_tags_all))

        for t in RESERVED_TAGS:
            unknown_tags.discard(t)

        if len(unknown_tags) > 0:
            for t in RESERVED_TAGS:
                unmatched_tags_all.discard(t)
            msg = 'tag(s) not found in playbook: %s.  possible values: %s'
            unknown = ','.join(sorted(unknown_tags))
            unmatched = ','.join(sorted(unmatched_tags_all))
            raise errors.AnsibleError(msg % (unknown, unmatched))

        for play in plays:
            ansible.callbacks.set_play(self.callbacks, play)
            ansible.callbacks.set_play(self.runner_callbacks, play)
            if not self._run_play(play):
                break

        ansible.callbacks.set_play(self.callbacks, None)
        ansible.callbacks.set_play(self.runner_callbacks, None)

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
            self.runner_callbacks.on_async_failed(host, reason, poller.runner.vars_cache[host]['ansible_job_id'])
            results['contacted'][host] = reason

        return results

    # *****************************************************

    def _trim_unavailable_hosts(self, hostlist=[], keep_failed=False):
        ''' returns a list of hosts that haven't failed and aren't dark '''

        return [ h for h in hostlist if (keep_failed or h not in self.stats.failures) and (h not in self.stats.dark)]

    # *****************************************************

    def _run_task_internal(self, task, include_failed=False):
        ''' run a particular module step in a playbook '''

        hosts = self._trim_unavailable_hosts(self.inventory.list_hosts(task.play._play_hosts), keep_failed=include_failed)
        self.inventory.restrict_to(hosts)

        runner = ansible.runner.Runner(
            pattern=task.play.hosts,
            inventory=self.inventory,
            module_name=task.module_name,
            module_args=task.module_args,
            forks=self.forks,
            remote_pass=self.remote_pass,
            module_path=self.module_path,
            timeout=self.timeout,
            remote_user=task.remote_user,
            remote_port=task.play.remote_port,
            module_vars=task.module_vars,
            play_vars=task.play_vars,
            play_file_vars=task.play_file_vars,
            role_vars=task.role_vars,
            role_params=task.role_params,
            default_vars=task.default_vars,
            extra_vars=self.extra_vars,
            private_key_file=self.private_key_file,
            setup_cache=self.SETUP_CACHE,
            vars_cache=self.VARS_CACHE,
            basedir=task.play.basedir,
            conditional=task.when,
            callbacks=self.runner_callbacks,
            transport=task.transport,
            is_playbook=True,
            check=self.check,
            diff=self.diff,
            environment=task.environment,
            complex_args=task.args,
            accelerate=task.play.accelerate,
            accelerate_port=task.play.accelerate_port,
            accelerate_ipv6=task.play.accelerate_ipv6,
            error_on_undefined_vars=C.DEFAULT_UNDEFINED_VAR_BEHAVIOR,
            vault_pass = self.vault_password,
            run_hosts=hosts,
            no_log=task.no_log,
            run_once=task.run_once,
            become=task.become,
            become_method=task.become_method,
            become_user=task.become_user,
            become_pass=task.become_pass,
        )

        runner.module_vars.update({'play_hosts': hosts})
        runner.module_vars.update({'ansible_version': self._ansible_version})

        if task.async_seconds == 0:
            results = runner.run()
        else:
            results, poller = runner.run_async(task.async_seconds)
            self.stats.compute(results)
            if task.async_poll_interval > 0:
                # if not polling, playbook requested fire and forget, so don't poll
                results = self._async_poll(poller, task.async_seconds, task.async_poll_interval)
            else:
                for (host, res) in results.get('contacted', {}).iteritems():
                    self.runner_callbacks.on_async_ok(host, res, poller.runner.vars_cache[host]['ansible_job_id'])

        contacted = results.get('contacted',{})
        dark      = results.get('dark', {})

        self.inventory.lift_restriction()

        if len(contacted.keys()) == 0 and len(dark.keys()) == 0:
            return None

        return results

    # *****************************************************

    def _run_task(self, play, task, is_handler):
        ''' run a single task in the playbook and recursively run any subtasks.  '''

        ansible.callbacks.set_task(self.callbacks, task)
        ansible.callbacks.set_task(self.runner_callbacks, task)

        if task.role_name:
            name = '%s | %s' % (task.role_name, task.name)
        else:
            name = task.name

        try:
            # v1 HACK: we don't have enough information to template many names
            # at this point.  Rather than making this work for all cases in
            # v1, just make this degrade gracefully.  Will fix in v2
            name = template(play.basedir, name, task.module_vars, lookup_fatal=False, filter_fatal=False)
        except:
            pass

        self.callbacks.on_task_start(name, is_handler)
        if hasattr(self.callbacks, 'skip_task') and self.callbacks.skip_task:
            ansible.callbacks.set_task(self.callbacks, None)
            ansible.callbacks.set_task(self.runner_callbacks, None)
            return True

        # template ignore_errors
        # TODO: Is this needed here?  cond is templated again in
        # check_conditional after some more manipulations.
        # TODO: we don't have enough information here to template cond either
        # (see note on templating name above)
        cond = template(play.basedir, task.ignore_errors, task.module_vars, expand_lists=False)
        task.ignore_errors =  utils.check_conditional(cond, play.basedir, task.module_vars, fail_on_undefined=C.DEFAULT_UNDEFINED_VAR_BEHAVIOR)

        # load up an appropriate ansible runner to run the task in parallel
        include_failed = is_handler and play.force_handlers
        results = self._run_task_internal(task, include_failed=include_failed)

        # if no hosts are matched, carry on
        hosts_remaining = True
        if results is None:
            hosts_remaining = False
            results = {}

        contacted = results.get('contacted', {})
        self.stats.compute(results, ignore_errors=task.ignore_errors)

        def _register_play_vars(host, result):
            # when 'register' is used, persist the result in the vars cache
            # rather than the setup cache - vars should be transient between
            # playbook executions
            if 'stdout' in result and 'stdout_lines' not in result:
                result['stdout_lines'] = result['stdout'].splitlines()
            utils.update_hash(self.VARS_CACHE, host, {task.register: result})

        def _save_play_facts(host, facts):
            # saves play facts in SETUP_CACHE, unless the module executed was
            # set_fact, in which case we add them to the VARS_CACHE
            if task.module_name in ('set_fact', 'include_vars'):
                utils.update_hash(self.VARS_CACHE, host, facts)
            else:
                utils.update_hash(self.SETUP_CACHE, host, facts)

        # add facts to the global setup cache
        for host, result in contacted.iteritems():
            if 'results' in result:
                # task ran with_ lookup plugin, so facts are encapsulated in
                # multiple list items in the results key
                for res in result['results']:
                    if type(res) == dict:
                        facts = res.get('ansible_facts', {})
                        _save_play_facts(host, facts)
            else:
                # when facts are returned, persist them in the setup cache
                facts = result.get('ansible_facts', {})
                _save_play_facts(host, facts)

            # if requested, save the result into the registered variable name
            if task.register:
                _register_play_vars(host, result)

        # also have to register some failed, but ignored, tasks
        if task.ignore_errors and task.register:
            failed = results.get('failed', {})
            for host, result in failed.iteritems():
                _register_play_vars(host, result)

        # flag which notify handlers need to be run
        if task.notify and len(task.notify) > 0:
            for host, results in results.get('contacted',{}).iteritems():
                if results.get('changed', False):
                    for handler_name in task.notify:
                        self._flag_handler(play, template(play.basedir, handler_name, task.module_vars), host)

        ansible.callbacks.set_task(self.callbacks, None)
        ansible.callbacks.set_task(self.runner_callbacks, None)
        return hosts_remaining

    # *****************************************************

    def _flag_handler(self, play, handler_name, host):
        '''
        if a task has any notify elements, flag handlers for run
        at end of execution cycle for hosts that have indicated
        changes have been made
        '''

        found = False
        for x in play.handlers():
            if handler_name == template(play.basedir, x.name, x.module_vars):
                found = True
                self.callbacks.on_notify(host, x.name)
                x.notified_by.append(host)
        if not found:
            raise errors.AnsibleError("change handler (%s) is not defined" % handler_name)

    # *****************************************************

    def _do_setup_step(self, play):
        ''' get facts from the remote system '''

        host_list = self._trim_unavailable_hosts(play._play_hosts)

        if play.gather_facts is None and C.DEFAULT_GATHERING == 'smart':
            host_list = [h for h in host_list if h not in self.SETUP_CACHE or 'module_setup' not in self.SETUP_CACHE[h]]
            if len(host_list) == 0:
                return {}
        elif play.gather_facts is False or (play.gather_facts is None and C.DEFAULT_GATHERING == 'explicit'):
            return {}

        self.callbacks.on_setup()
        self.inventory.restrict_to(host_list)

        ansible.callbacks.set_task(self.callbacks, None)
        ansible.callbacks.set_task(self.runner_callbacks, None)

        # push any variables down to the system
        setup_results = ansible.runner.Runner(
            basedir=self.basedir,
            pattern=play.hosts,
            module_name='setup',
            module_args={},
            inventory=self.inventory,
            forks=self.forks,
            module_path=self.module_path,
            timeout=self.timeout,
            remote_user=play.remote_user,
            remote_pass=self.remote_pass,
            remote_port=play.remote_port,
            private_key_file=self.private_key_file,
            setup_cache=self.SETUP_CACHE,
            vars_cache=self.VARS_CACHE,
            callbacks=self.runner_callbacks,
            become=play.become,
            become_method=play.become_method,
            become_user=play.become_user,
            become_pass=self.become_pass,
            vault_pass=self.vault_password,
            transport=play.transport,
            is_playbook=True,
            module_vars=play.vars,
            play_vars=play.vars,
            play_file_vars=play.vars_file_vars,
            role_vars=play.role_vars,
            default_vars=play.default_vars,
            check=self.check,
            diff=self.diff,
            accelerate=play.accelerate,
            accelerate_port=play.accelerate_port,
        ).run()
        self.stats.compute(setup_results, setup=True)

        self.inventory.lift_restriction()

        # now for each result, load into the setup cache so we can
        # let runner template out future commands
        setup_ok = setup_results.get('contacted', {})
        for (host, result) in setup_ok.iteritems():
            utils.update_hash(self.SETUP_CACHE, host, {'module_setup': True})
            utils.update_hash(self.SETUP_CACHE, host, result.get('ansible_facts', {}))
        return setup_results

    # *****************************************************


    def generate_retry_inventory(self, replay_hosts):
        '''
        called by /usr/bin/ansible when a playbook run fails. It generates an inventory
        that allows re-running on ONLY the failed hosts.  This may duplicate some
        variable information in group_vars/host_vars but that is ok, and expected.
        '''

        buf = StringIO.StringIO()
        for x in replay_hosts:
            buf.write("%s\n" % x)
        basedir = C.shell_expand_path(C.RETRY_FILES_SAVE_PATH)
        filename = "%s.retry" % os.path.basename(self.filename)
        filename = filename.replace(".yml","")
        filename = os.path.join(basedir, filename)

        try:
            if not os.path.exists(basedir):
                os.makedirs(basedir)

            fd = open(filename, 'w')
            fd.write(buf.getvalue())
            fd.close()
        except:
            ansible.callbacks.display(
                "\nERROR: could not create retry file. Check the value of \n"
                + "the configuration variable 'retry_files_save_path' or set \n"
                + "'retry_files_enabled' to False to avoid this message.\n",
                color='red'
            )
            return None

        return filename

    # *****************************************************
    def tasks_to_run_in_play(self, play):

        tasks = []

        for task in play.tasks():
            # only run the task if the requested tags match or has 'always' tag
            u = set(['untagged'])
            task_set = set(task.tags)

            if 'always' in task.tags:
                should_run = True
            else:
                if 'all' in self.only_tags:
                    should_run = True
                else:
                    should_run = False
                    if  'tagged' in self.only_tags:
                        if task_set != u:
                            should_run = True
                    elif 'untagged' in self.only_tags:
                        if task_set == u:
                            should_run = True
                    else:
                        if task_set.intersection(self.only_tags):
                            should_run = True

            # Check for tags that we need to skip
            if 'all' in self.skip_tags:
                should_run = False
            else:
                if 'tagged' in self.skip_tags:
                    if task_set != u:
                        should_run = False
                elif 'untagged' in self.skip_tags:
                    if task_set == u:
                        should_run = False
                else:
                    if should_run:
                        if task_set.intersection(self.skip_tags):
                            should_run = False

            if should_run:
                tasks.append(task)

        return tasks

    # *****************************************************
    def _run_play(self, play):
        ''' run a list of tasks for a given pattern, in order '''

        self.callbacks.on_play_start(play.name)
        # Get the hosts for this play
        play._play_hosts = self.inventory.list_hosts(play.hosts)
        # if no hosts matches this play, drop out
        if not play._play_hosts:
            self.callbacks.on_no_hosts_matched()
            return True

        # get facts from system
        self._do_setup_step(play)

        # now with that data, handle contentional variable file imports!
        all_hosts = self._trim_unavailable_hosts(play._play_hosts)
        play.update_vars_files(all_hosts, vault_password=self.vault_password)
        hosts_count = len(all_hosts)

        if play.serial.endswith("%"):

            # This is a percentage, so calculate it based on the
            # number of hosts
            serial_pct = int(play.serial.replace("%",""))
            serial = int((serial_pct/100.0) * len(all_hosts))

            # Ensure that no matter how small the percentage, serial
            # can never fall below 1, so that things actually happen
            serial = max(serial, 1)
        else:
            serial = int(play.serial)

        serialized_batch = []
        if serial <= 0:
            serialized_batch = [all_hosts]
        else:
            # do N forks all the way through before moving to next
            while len(all_hosts) > 0:
                play_hosts = []
                for x in range(serial):
                    if len(all_hosts) > 0:
                        play_hosts.append(all_hosts.pop(0))
                serialized_batch.append(play_hosts)

        task_errors = False
        for on_hosts in serialized_batch:

            # restrict the play to just the hosts we have in our on_hosts block that are
            # available.
            play._play_hosts = self._trim_unavailable_hosts(on_hosts)
            self.inventory.also_restrict_to(on_hosts)

            for task in self.tasks_to_run_in_play(play):

                if task.meta is not None:
                    # meta tasks can force handlers to run mid-play
                    if task.meta == 'flush_handlers':
                        self.run_handlers(play)

                    # skip calling the handler till the play is finished
                    continue

                if not self._run_task(play, task, False):
                    # whether no hosts matched is fatal or not depends if it was on the initial step.
                    # if we got exactly no hosts on the first step (setup!) then the host group
                    # just didn't match anything and that's ok
                    return False

                # Get a new list of what hosts are left as available, the ones that
                # did not go fail/dark during the task
                host_list = self._trim_unavailable_hosts(play._play_hosts)

                # Set max_fail_pct to 0, So if any hosts fails, bail out
                if task.any_errors_fatal and len(host_list) < hosts_count:
                    play.max_fail_pct = 0

                # If threshold for max nodes failed is exceeded, bail out.
                if play.serial > 0:
                    # if serial is set, we need to shorten the size of host_count
                    play_count = len(play._play_hosts)
                    if (play_count - len(host_list)) > int((play.max_fail_pct)/100.0 * play_count):
                        host_list = None
                else:
                    if (hosts_count - len(host_list)) > int((play.max_fail_pct)/100.0 * hosts_count):
                        host_list = None

                # if no hosts remain, drop out
                if not host_list:
                    if play.force_handlers:
                        task_errors = True
                        break
                    else:
                        self.callbacks.on_no_hosts_remaining()
                        return False

            # lift restrictions after each play finishes
            self.inventory.lift_also_restriction()

            if task_errors and not play.force_handlers:
                # if there were failed tasks and handler execution
                # is not forced, quit the play with an error
                return False
            else:
                # no errors, go ahead and execute all handlers
                if not self.run_handlers(play):
                    return False

        return True


    def run_handlers(self, play):
        on_hosts = play._play_hosts
        hosts_count = len(on_hosts)
        for task in play.tasks():
            if task.meta is not None:

                fired_names = {}
                for handler in play.handlers():
                    if len(handler.notified_by) > 0:
                        self.inventory.restrict_to(handler.notified_by)

                        # Resolve the variables first
                        handler_name = template(play.basedir, handler.name, handler.module_vars)
                        if handler_name not in fired_names:
                            self._run_task(play, handler, True)
                        # prevent duplicate handler includes from running more than once
                        fired_names[handler_name] = 1

                        host_list = self._trim_unavailable_hosts(play._play_hosts)
                        if handler.any_errors_fatal and len(host_list) < hosts_count:
                            play.max_fail_pct = 0
                        if (hosts_count - len(host_list)) > int((play.max_fail_pct)/100.0 * hosts_count):
                            host_list = None
                        if not host_list and not play.force_handlers:
                            self.callbacks.on_no_hosts_remaining()
                            return False

                        self.inventory.lift_restriction()
                        new_list = handler.notified_by[:]
                        for host in handler.notified_by:
                            if host in on_hosts:
                                while host in new_list:
                                    new_list.remove(host)
                        handler.notified_by = new_list

                continue

        return True
