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

#############################################

import ansible.runner
import ansible.constants as C
from ansible import utils
from ansible import errors
import shlex
import os
import time

# used to transfer variables to Runner
SETUP_CACHE={ }

#############################################

class PlayBook(object):

    '''
    runs an ansible playbook, given as a datastructure
    or YAML filename.  a playbook is a deployment, config
    management, or automation based set of commands to
    run in series.

    multiple plays/tasks do not execute simultaneously,
    but tasks in each pattern do execute in parallel
    (according to the number of forks requested) among
    the hosts they address
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
        remote_port      = C.DEFAULT_REMOTE_PORT,
        transport        = C.DEFAULT_TRANSPORT,
        override_hosts   = None,
        extra_vars       = None,
        debug            = False,
        verbose          = False,
        callbacks        = None,
        runner_callbacks = None,
        stats            = None):

        if playbook is None or callbacks is None or runner_callbacks is None or stats is None:
            raise Exception('missing required arguments')

        self.host_list        = host_list
        self.module_path      = module_path
        self.forks            = forks
        self.timeout          = timeout
        self.remote_user      = remote_user
        self.remote_pass      = remote_pass
        self.remote_port      = remote_port
        self.transport        = transport
        self.debug            = debug
        self.verbose          = verbose
        self.callbacks        = callbacks
        self.runner_callbacks = runner_callbacks
        self.override_hosts   = override_hosts
        self.extra_vars       = extra_vars
        self.stats            = stats

        self.basedir = os.path.dirname(playbook)
        self.playbook = self._parse_playbook(playbook)

        self.host_list, self.groups = ansible.runner.Runner.parse_hosts(
            host_list, override_hosts=self.override_hosts, extra_vars=self.extra_vars)
   
    # *****************************************************

    def _get_vars(self, play, dirname):
        ''' load the vars section from a play '''
        if play.get('vars') is None:
            play['vars'] = {}
        vars = play['vars']
        if type(vars) != dict:
            raise errors.AnsibleError("'vars' section must contain only key/value pairs")
        vars_prompt = play.get('vars_prompt', {})
        if type(vars_prompt) != dict:
            raise errors.AnsibleError("'vars_prompt' section must contain only key/value pairs")
        for vname in vars_prompt:
            print vars_prompt[vname]
            # FIXME - need some way to know that this prompt should be getpass or raw_input
            vars[vname] = self.callbacks.on_vars_prompt(vname)
        return vars

    # *****************************************************

    def _include_tasks(self, play, task, dirname, new_tasks):
        ''' load tasks included from external files. '''

        # include: some.yml a=2 b=3 c=4
        include_tokens = task['include'].split()
        path = utils.path_dwim(dirname, include_tokens[0])
        play_vars = self._get_vars(play, dirname)
        include_vars = {}
        for i,x in enumerate(include_tokens):
            if x.find("=") != -1:
                (k,v) = x.split("=")
                include_vars[k] = v
        inject_vars = play_vars.copy()
        inject_vars.update(include_vars)
        included = utils.template_from_file(path, inject_vars)
        included = utils.parse_yaml(included)
        for x in included:
            if len(include_vars):
                x["vars"] = include_vars
            new_tasks.append(x)

    # *****************************************************

    def _include_handlers(self, play, handler, dirname, new_handlers):
        ''' load handlers from external files '''

        path = utils.path_dwim(dirname, handler['include'])
        inject_vars = self._get_vars(play, dirname)
        included = utils.template_from_file(path, inject_vars)
        included = utils.parse_yaml(included)
        for x in included:
            new_handlers.append(x)

    # *****************************************************

    def _parse_playbook(self, playbook):
        ''' load YAML file, including handling for imported files '''
        
        dirname  = os.path.dirname(playbook)
        playbook = utils.parse_yaml_from_file(playbook)

        for play in playbook:
            tasks = play.get('tasks',[])
            handlers = play.get('handlers', [])

            # process tasks in this file as well as imported tasks
            new_tasks = []
            for task in tasks:
                if 'include' in task:
                    self._include_tasks(play, task, dirname, new_tasks)
                else:
                    new_tasks.append(task)
            play['tasks'] = new_tasks

            # process handlers as well as imported handlers
            new_handlers = [] 
            for handler in handlers:
                if 'include' in handler:
                    self._include_handlers(play, handler, dirname, new_handlers)
                else:
                    new_handlers.append(handler)
            play['handlers'] = new_handlers

        return playbook

    # *****************************************************
        
    def run(self):
        ''' run all patterns in the playbook '''

        # loop through all patterns and run them
        self.callbacks.on_start()
        for pattern in self.playbook:
            self._run_play(pattern)

        # summarize the results
        results = {}
        for host in self.stats.processed.keys():
            results[host] = self.stats.summarize(host)
        return results

    # *****************************************************

    def hosts_to_poll(self, results):
        ''' which hosts need more polling? '''

        hosts = []
        for (host, res) in results['contacted'].iteritems():
            if (host in self.stats.failures) or (host in self.stats.dark):
                continue
            if not 'finished' in res and not 'skipped' in res and 'started' in res:
                hosts.append(host)
        return hosts

    # *****************************************************

    def _async_poll(self, runner, hosts, async_seconds, async_poll_interval, only_if):
        ''' launch an async job, if poll_interval is set, wait for completion '''

        runner.host_list = hosts
        runner.background = async_seconds
        results = runner.run()
        self.stats.compute(results, poll=True)

        if async_poll_interval <= 0:
            # if not polling, playbook requested fire and forget
            # trust the user wanted that and return immediately
            return results
        
        poll_hosts = results['contacted'].keys()
        if len(poll_hosts) == 0:
            # no hosts launched ok, return that.
            return results
        ahost = poll_hosts[0]

        jid = results['contacted'][ahost].get('ansible_job_id', None)

        if jid is None:
            # note: this really shouldn't happen, ever
            self.callbacks.on_async_confused("unexpected error: unable to determine jid")
            return results

        clock = async_seconds
        runner.host_list = self.hosts_to_poll(results)

        poll_results = results
        while (clock >= 0):

            # poll/loop until polling duration complete
            runner.module_args = "jid=%s" % jid
            runner.module_name = 'async_status'
            runner.background  = 0  
            runner.pattern     = '*'
            poll_results       = runner.run()
            self.stats.compute(poll_results, poll=True)
            runner.host_list       = self.hosts_to_poll(poll_results)

            if len(runner.host_list) == 0:
                break
            if poll_results is None:
                break

            # mention which hosts we're going to poll again...
            for (host, host_result) in poll_results['contacted'].iteritems():
                results['contacted'][host] = host_result
                if not host in self.stats.dark and not host in self.stats.failures:
                    self.callbacks.on_async_poll(jid, host, clock, host_result)

            # run down the clock
            clock = clock - async_poll_interval
            time.sleep(async_poll_interval)

        # mark any hosts that are still listed as started as failed
        # since these likely got killed by async_wrapper
        for (host, host_result) in poll_results['contacted'].iteritems():
            if 'started' in host_result:
                reason = { 'failed' : 1, 'rc' : None, 'msg' : 'timed out' }
                self.runner_callbacks.on_failed(host, reason)
                results['contacted'][host] = reason

        return results

    # *****************************************************

    def _run_module(self, pattern, host_list, module, args, vars, remote_user, 
        async_seconds, async_poll_interval, only_if, sudo, transport):
        ''' run a particular module step in a playbook '''

        hosts = [ h for h in host_list if (h not in self.stats.failures) and (h not in self.stats.dark)]

        runner = ansible.runner.Runner(
            pattern=pattern, groups=self.groups, module_name=module,
            module_args=args, host_list=hosts, forks=self.forks,
            remote_pass=self.remote_pass, module_path=self.module_path,
            timeout=self.timeout, remote_user=remote_user, 
            remote_port=self.remote_port, module_vars=vars,
            setup_cache=SETUP_CACHE, basedir=self.basedir,
            conditional=only_if, callbacks=self.runner_callbacks, 
            extra_vars=self.extra_vars, debug=self.debug, sudo=sudo,
            transport=transport
        )

        if async_seconds == 0:
            return runner.run()
        else:
            return self._async_poll(runner, hosts, async_seconds, async_poll_interval, only_if)

    # *****************************************************

    def _run_task(self, pattern=None, host_list=None, task=None, 
        remote_user=None, handlers=None, conditional=False, sudo=False, transport=None):
        ''' run a single task in the playbook and recursively run any subtasks.  '''

        # load the module name and parameters from the task entry
        name    = task.get('name', None) 
        action  = task.get('action', None)
        if action is None:
            raise errors.AnsibleError("action is required for each item in tasks: offending task is %s" % name if name else "unknown")
        if name is None:
            name = action
        only_if = task.get('only_if', 'True')
        async_seconds = int(task.get('async', 0))  # not async by default
        async_poll_interval = int(task.get('poll', 10))  # default poll = 10 seconds

        tokens = action.split(None, 1)
        module_name = tokens[0]
        module_args = tokens[1]

        # include task specific vars
        module_vars = task.get('vars')

        # tasks can be direct (run on all nodes matching
        # the pattern) or conditional, where they ran
        # as the result of a change handler on a subset
        # of all of the hosts

        self.callbacks.on_task_start(name, conditional)

        # load up an appropriate ansible runner to
        # run the task in parallel
        results = self._run_module(pattern, host_list, module_name, 
            module_args, module_vars, remote_user, async_seconds, 
            async_poll_interval, only_if, sudo, transport)

        self.stats.compute(results)

        # if no hosts are matched, carry on, unlike /bin/ansible
        # which would warn you about this
        if results is None:
            results = {}
 
        # flag which notify handlers need to be run
        # this will be on a SUBSET of the actual host list.  For instance
        # a file might need to be written on only half of the nodes so
        # we would only trigger restarting Apache on half of the nodes

        subtasks = task.get('notify', [])
        if len(subtasks) > 0:
            for host, results in results.get('contacted',{}).iteritems():
                if results.get('changed', False):
                    for subtask in subtasks:
                        self._flag_handler(handlers, subtask, host)

    # *****************************************************

    def _flag_handler(self, handlers, match_name, host):
        ''' 
        if a task has any notify elements, flag handlers for run
        at end of execution cycle for hosts that have indicated
        changes have been made
        '''

        # for all registered handlers in the ansible playbook
        # for this particular pattern group

        found = False
        for x in handlers:
            name = x.get('name', None)
            if name is None:
                raise errors.AnsibleError('handler is missing a name')
            if match_name == name:
                found = True
                self.callbacks.on_notify(host, name)
                # flag the handler with the list of hosts it needs to be run on, it will be run later
                if not 'run' in x:
                    x['run'] = []
                x['run'].append(host)
        if not found:
            raise errors.AnsibleError("change handler (%s) is not defined" % match_name)

    # *****************************************************

    def _do_conditional_imports(self, vars_files, host_list):
        ''' handle the vars_files section, which can contain variables '''
        
        # FIXME: save parsed variable results in memory to avoid excessive re-reading/parsing
        # FIXME: currently parses imports for hosts not in the pattern, that is not wrong, but it's 
        #        not super optimized yet either, because we wouldn't have hit them, ergo
        #        it will raise false errors if there is no defaults variable file without any $vars
        #        in it, which could happen on uncontacted hosts.
 
        if type(vars_files) != list:
            raise errors.AnsibleError("vars_files must be a list")
        for host in host_list:
            cache_vars = SETUP_CACHE.get(host,{}) 
            SETUP_CACHE[host] = cache_vars
            for filename in vars_files:
                if type(filename) == list:
                    # loop over all filenames, loading the first one, and failing if # none found
                    found = False
                    sequence = []
                    for real_filename in filename:
                        filename2 = utils.path_dwim(self.basedir, utils.template(real_filename, cache_vars))
                        sequence.append(filename2)
                        if os.path.exists(filename2):
                            found = True
                            data = utils.parse_yaml_from_file(filename2)
                            SETUP_CACHE[host].update(data)
                            self.callbacks.on_import_for_host(host, filename2)
                            break
                        else:
                            self.callbacks.on_not_import_for_host(host, filename2)
                    if not found:
                        raise errors.AnsibleError(
                            "%s: FATAL, no files matched for vars_files import sequence: %s" % (host, sequence)
                        )

                else:
                    filename2 = utils.path_dwim(self.basedir, utils.template(filename, cache_vars))
                    if not os.path.exists(filename2):
                        raise errors.AnsibleError("no file matched for vars_file import: %s" % filename2)
                    data = utils.parse_yaml_from_file(filename2)
                    SETUP_CACHE[host].update(data)
                    self.callbacks.on_import_for_host(host, filename2)

    # *****************************************************

    def _do_setup_step(self, pattern, vars, user, port, sudo, transport, vars_files=None):
        ''' push variables down to the systems and get variables+facts back up '''

        # this enables conditional includes like $facter_os.yml and is only done
        # after the original pass when we have that data.
        #

        if vars_files is not None:
            self.callbacks.on_setup_secondary()
            self._do_conditional_imports(vars_files, self.host_list)
        else:
            self.callbacks.on_setup_primary()

        host_list = [ h for h in self.host_list if not (h in self.stats.failures or h in self.stats.dark) ]

        # push any variables down to the system
        setup_results = ansible.runner.Runner(
            pattern=pattern, groups=self.groups, module_name='setup',
            module_args=vars, host_list=host_list,
            forks=self.forks, module_path=self.module_path,
            timeout=self.timeout, remote_user=user,
            remote_pass=self.remote_pass, remote_port=self.remote_port,
            setup_cache=SETUP_CACHE,
            callbacks=self.runner_callbacks, sudo=sudo, debug=self.debug,
            transport=transport,
        ).run()
        self.stats.compute(setup_results, setup=True)

        # now for each result, load into the setup cache so we can
        # let runner template out future commands
        setup_ok = setup_results.get('contacted', {})
        if vars_files is None:
            # first pass only or we'll erase good work
            for (host, result) in setup_ok.iteritems():
                SETUP_CACHE[host] = result

        if self.extra_vars:
            extra_vars = utils.parse_kv(self.extra_vars)
            for h in self.host_list:
                try:
                    SETUP_CACHE[h].update(extra_vars)
                except:
                    SETUP_CACHE[h] = extra_vars
        return host_list

    # *****************************************************

    def _run_play(self, pg):
        ''' run a list of tasks for a given pattern, in order '''

        # get configuration information about the pattern
        pattern  = pg.get('hosts',None)
        if self.override_hosts:
            pattern = 'all'
        if pattern is None:
            raise errors.AnsibleError('hosts declaration is required')

        vars       = self._get_vars(pg, self.basedir)
        vars_files = pg.get('vars_files', {})
        tasks      = pg.get('tasks', [])
        handlers   = pg.get('handlers', [])
        user       = pg.get('user', self.remote_user)
        port       = pg.get('port', self.remote_port)
        sudo       = pg.get('sudo', False)
        transport  = pg.get('connection', self.transport)

        self.callbacks.on_play_start(pattern)

        # push any variables down to the system # and get facts/ohai/other data back up
        self._do_setup_step(pattern, vars, user, port, sudo, transport, None)
         
        # now with that data, handle contentional variable file imports!
        if len(vars_files) > 0:
            self._do_setup_step(pattern, vars, user, port, sudo, transport, vars_files)

        # run all the top level tasks, these get run on every node
        for task in tasks:
            self._run_task(
                pattern=pattern,
                host_list=self.host_list,
                task=task, 
                handlers=handlers,
                remote_user=user,
                sudo=sudo,
                transport=transport
            )

        # handlers only run on certain nodes, they are flagged by _flag_handlers
        # above.  They only run on nodes when things mark them as changed, and
        # handlers only get run once.  For instance, the system is designed
        # such that multiple config files if changed can ask for an Apache restart
        # but Apache will only be restarted once (at the end).

        for task in handlers:
            triggered_by = task.get('run', None)
            if type(triggered_by) == list:
                self._run_task(
                   pattern=pattern, 
                   task=task,
                   handlers=[],
                   host_list=triggered_by,
                   conditional=True,
                   remote_user=user,
                   sudo=sudo,
                   transport=transport
                )

        # end of execution for this particular pattern.  Multiple patterns
        # can be in a single playbook file

 

