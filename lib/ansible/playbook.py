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
from ansible.utils import *
from ansible.errors import *
import yaml
import shlex
import os
import jinja2
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

    multiple patterns do not execute simultaneously,
    but tasks in each pattern do execute in parallel
    according to the number of forks requested.
    '''

    def __init__(self,
        playbook     =None,
        host_list    =C.DEFAULT_HOST_LIST,
        module_path  =C.DEFAULT_MODULE_PATH,
        forks        =C.DEFAULT_FORKS,
        timeout      =C.DEFAULT_TIMEOUT,
        remote_user  =C.DEFAULT_REMOTE_USER,
        remote_pass  =C.DEFAULT_REMOTE_PASS,
        verbose=False,
        callbacks=None):

        # TODO, once ansible-playbook is it's own script this will
        # have much LESS parameters to the constructor and will
        # read most everything per pattern from the playbook
        # and this will be greatly simplified

        self.host_list   = host_list
        self.module_path = module_path
        self.forks       = forks
        self.timeout     = timeout
        self.remote_user = remote_user
        self.remote_pass = remote_pass
        self.verbose     = verbose
        self.callbacks   = callbacks
        self.callbacks.set_playbook(self)

        # store the list of changes/invocations/failure counts
        # as a dictionary of integers keyed off the hostname

        self.processed    = {}
        self.dark         = {}
        self.changed      = {}
        self.invocations  = {}
        self.failures     = {}

        # playbook file can be passed in as a path or
        # as file contents (to support API usage)

        self.basedir = os.path.dirname(playbook)
        self.playbook = self._parse_playbook(playbook)

    def _get_vars(self, play, dirname):
        vars = play.get('vars', {})
        if type(vars) != dict:
            raise AnsibleError("'vars' section must contain only key/value pairs")
        vars_files = play.get('vars_files', [])
        for f in vars_files:
            path = path_dwim(dirname, f)
            # FIXME: better error handling if not valid YAML 
            # or file not found
            # raise typed exception
            data = file(path).read()
            data = yaml.load(data)
            vars.update(data)
        return vars

    def _include_tasks(self, play, task, dirname, new_tasks):
        # an include line looks like:
        # include: some.yml a=2 b=3 c=4
        include_tokens = task['include'].split()
        path = path_dwim(dirname, include_tokens[0])
        inject_vars = self._get_vars(play, dirname)
        for i,x in enumerate(include_tokens):
            if x.find("=") != -1:
                (k,v) = x.split("=")
                inject_vars[k] = v
            included = file(path).read()
            template = jinja2.Template(included)
            included = template.render(inject_vars)
            included = yaml.load(included)
            for x in included:
                new_tasks.append(x)

    def _include_handlers(self, play, handler, dirname, new_handlers):
        path = path_dwim(dirname, handler['include'])
        included = file(path).read()
        inject_vars = self._get_vars(play, dirname)
        template = jinja2.Template(included)
        included = template.render(inject_vars)
        included = yaml.load(included)
        for x in included:
            new_handlers.append(x)

    def _parse_playbook(self, playbook):
        ''' load YAML file, including handling for imported files '''
        
        dirname  = os.path.dirname(playbook)
        playbook = yaml.load(file(playbook).read())

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
        
    def run(self):
        ''' run all patterns in the playbook '''

        # loop through all patterns and run them
        self.callbacks.on_start()
        for pattern in self.playbook:
            self._run_play(pattern)

        # summarize the results
        results = {}
        for host in self.processed.keys():
            results[host]  = {
                'resources'   : self.invocations.get(host, 0),
                'changed'     : self.changed.get(host, 0),
                'dark'        : self.dark.get(host, 0),
                'failed'      : self.failures.get(host, 0)
            }
        return results

    def _prune_failed_hosts(self, host_list):
        new_hosts = []
        for x in host_list:
            if not x in self.failures and not x in self.dark:
                new_hosts.append(x)
        return new_hosts

    def hosts_to_poll(self, results):
        ''' which hosts need more polling? '''
        hosts = []
        for (host, res) in results['contacted'].iteritems():
            # FIXME: make polling pattern in /bin/ansible match
            # move to common function in utils
            if not 'finished' in res and 'started' in res:
                hosts.append(host)
        return hosts


    def _async_poll(self, runner, async_seconds, async_poll_interval):
        ''' launch an async job, if poll_interval is set, wait for completion '''

        # TODO: refactor this function
        runner.background = async_seconds
        results = runner.run()

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
            # FIXME this really shouldn't happen.  consider marking hosts failed
            # and looking for jid in other host.
            self.callbacks.on_async_confused("unexpected error: unable to determine jid")
            return results

        clock = async_seconds
        runner.hosts       = self.hosts_to_poll(results)
        poll_results = results
        while (clock >= 0):
            runner.hosts = poll_hosts
            # FIXME: make a "get_async_runner" method like in /bin/ansible
            # loop until polling duration complete
            runner.module_args = [ "jid=%s" % jid ]
            runner.module_name = 'async_status'
            # FIXME: make it such that if you say 'async_status' you
            # can't background that op!
            runner.background  = 0  
            runner.pattern     = '*'
            runner.hosts       = self.hosts_to_poll(poll_results)
            poll_results       = runner.run()
            if len(runner.hosts) == 0:
                break
            if poll_results is None:
                break
            for (host, host_result) in poll_results['contacted'].iteritems():
                # override last result with current status result for report
                results['contacted'][host] = host_result
                # output if requested
                self.callbacks.on_async_poll(jid, host, clock, host_result)
                # run down the clock
                clock = clock - async_poll_interval
                time.sleep(async_poll_interval)
                # do not have to poll the completed hosts, smaller list
                runner.hosts       = self.hosts_to_poll(poll_results)
            # mark any hosts that are still listed as started as failed
            # since these likely got killed by async_wrapper
            for (host, host_result) in results['contacted'].iteritems():
                if 'started' in host_result:
                    results['contacted'][host] = { 'failed' : 1, 'rc' : None, 'msg' : 'timed out' }
        return results

    def _run_module(self, pattern, module, args, hosts, remote_user,
        async_seconds, async_poll_interval):

        ''' run a particular module step in a playbook '''
        runner = ansible.runner.Runner(
            pattern=pattern,
            module_name=module,
            module_args=args,
            host_list=hosts,
            forks=self.forks,
            remote_pass=self.remote_pass,
            module_path=self.module_path,
            timeout=self.timeout,
            remote_user=remote_user,
            setup_cache=SETUP_CACHE,
            basedir=self.basedir
        )

        if async_seconds == 0:
            return runner.run()
        else:
            return self._async_poll(runner, async_seconds, async_poll_interval)

    def _run_task(self, pattern=None, task=None, host_list=None,
        remote_user=None, handlers=None, conditional=False):
        '''
        run a single task in the playbook and
        recursively run any subtasks.
        '''

        if host_list is None:
            # pruned host lists occur when running triggered
            # actions where not all hosts have changed
            # though top-level tasks will pass in "None" here
            host_list = self.host_list
            (host_list, groups) = ansible.runner.Runner.parse_hosts(host_list)

        # do not continue to run tasks on hosts that have had failures
        host_list = self._prune_failed_hosts(host_list)

        # load the module name and parameters from the task entry
        name    = task['name']
        action  = task['action']
        async_seconds = int(task.get('async', 0)) # not async by default
        async_poll_interval = int(task.get('poll', 10)) # default poll = 10 seconds

        # comment = task.get('comment', '')

        tokens = shlex.split(action)
        module_name = tokens[0]
        module_args = tokens[1:]

        # tasks can be direct (run on all nodes matching
        # the pattern) or conditional, where they ran
        # as the result of a change handler on a subset
        # of all of the hosts

        self.callbacks.on_task_start(name, conditional)

        # load up an appropriate ansible runner to
        # run the task in parallel
        results = self._run_module(pattern, module_name, 
            module_args, host_list, remote_user, 
            async_seconds, async_poll_interval)

        # if no hosts are matched, carry on, unlike /bin/ansible
        # which would warn you about this
        if results is None:
            results = {}
 
        # walk through the results and build up
        # summary information about successes and
        # failures.  TODO: split into subfunction

        dark      = results.get("dark", {})
        contacted = results.get("contacted", {})

        for host, msg in dark.items():
            self.processed[host] = 1
            self.callbacks.on_unreachable(host, msg)
            if not host in self.dark:
                self.dark[host] = 1
            else:
                self.dark[host] = self.dark[host] + 1

        for host, results in contacted.items():
            self.processed[host] = 1
   
            if is_failed(results):
                self.callbacks.on_failed(host, results)
                if not host in self.failures:
                    self.failures[host] = 1
                else:
                    self.failures[host] = self.failures[host] + 1
            else:
                self.callbacks.on_ok(host)
                if not host in self.invocations:
                    self.invocations[host] = 1
                else:
                    self.invocations[host] = self.invocations[host] + 1
                if results.get('changed', False):
                    if not host in self.changed:
                        self.changed[host] = 1
                    else:
                        self.changed[host] = self.changed[host] + 1

        # flag which notify handlers need to be run
        # this will be on a SUBSET of the actual host list.  For instance
        # a file might need to be written on only half of the nodes so
        # we would only trigger restarting Apache on half of the nodes

        subtasks = task.get('notify', [])
        if len(subtasks) > 0:
            for host, results in contacted.items():
                if results.get('changed', False):
                    for subtask in subtasks:
                        self._flag_handler(handlers, subtask, host)

    def _flag_handler(self, handlers, match_name, host):
        ''' 
        if a task has any notify elements, flag handlers for run
        at end of execution cycle for hosts that have indicated
        changes have been made
        '''

        # for all registered handlers in the ansible playbook
        # for this particular pattern group

        for x in handlers:
            name = x['name']
            if match_name == name:
                # flag the handler with the list of hosts
                # it needs to be run on, it will be run later
                if not 'run' in x:
                    x['run'] = []
                x['run'].append(host)

    def _run_play(self, pg):
        '''
        run a list of tasks for a given pattern, in order
        '''

        # get configuration information about the pattern
        pattern  = pg['hosts']

        vars     = self._get_vars(pg, self.basedir)
        tasks    = pg['tasks']
        handlers = pg['handlers']
        user     = pg.get('user', C.DEFAULT_REMOTE_USER)

        self.host_list, groups = ansible.runner.Runner.parse_hosts(self.host_list)

        self.callbacks.on_play_start(pattern)

        # first run the setup task on every node, which gets the variables
        # written to the JSON file and will also bubble facts back up via
        # magic in Runner()
        push_var_str=''
        for (k,v) in vars.items():
            push_var_str += "%s=%s " % (k,v)

        # push any variables down to the system
        setup_results = ansible.runner.Runner(
            pattern=pattern,
            module_name='setup',
            module_args=push_var_str,
            host_list=self.host_list,
            forks=self.forks,
            module_path=self.module_path,
            timeout=self.timeout,
            remote_user=user,
            setup_cache=SETUP_CACHE
        ).run()

        # now for each result, load into the setup cache so we can
        # let runner template out future commands
        setup_ok = setup_results.get('contacted', {})
        for (host, result) in setup_ok.items():
            SETUP_CACHE[host] = result

        # run all the top level tasks, these get run on every node
        for task in tasks:
            self._run_task(
                pattern=pattern, 
                task=task, 
                handlers=handlers,
                remote_user=user
            )

        # handlers only run on certain nodes, they are flagged by _flag_handlers
        # above.  They only run on nodes when things mark them as changed, and
        # handlers only get run once.  For instance, the system is designed
        # such that multiple config files if changed can ask for an Apache restart
        # but Apache will only be restarted once (at the end).

        for task in handlers:
            if type(task.get("run", None)) == list:
                self._run_task(
                   pattern=pattern, 
                   task=task,
                   handlers=handlers,
                   host_list=task.get('run',[]),
                   conditional=True,
                   remote_user=user
                )

        # end of execution for this particular pattern.  Multiple patterns
        # can be in a single playbook file

 

