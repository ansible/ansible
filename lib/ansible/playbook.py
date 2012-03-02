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

import ansible.runner
import ansible.constants as C
import yaml
import shlex

# TODO: make a constants file rather than
# duplicating these

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
        verbose=False):

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

        # store the list of changes/invocations/failure counts
        # as a dictionary of integers keyed off the hostname

        self.processed    = {}
        self.dark         = {}
        self.changed      = {}
        self.invocations  = {}
        self.failures     = {}

        # playbook file can be passed in as a path or
        # as file contents (to support API usage)

        if type(playbook) == str:
            playbook = yaml.load(file(playbook).read())
        self.playbook = playbook
        
    def run(self):
        ''' run all patterns in the playbook '''

        # loop through all patterns and run them
        for pattern in self.playbook:
            self._run_pattern(pattern)
        if self.verbose:
            print "\n"

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
        new_hosts = []
        for x in host_list:
            if not self.failures.has_key(x) and not self.dark.has_key(x):
                new_hosts.append(x)
        host_list = new_hosts

        # load the module name and parameters from the task
        # entry
        name    = task['name']
        action  = task['action']
        comment = task.get('comment', '')

        tokens = shlex.split(action)
        module_name = tokens[0]
        module_args = tokens[1:]

        # tasks can be direct (run on all nodes matching
        # the pattern) or conditional, where they ran
        # as the result of a change handler on a subset
        # of all of the hosts

        if self.verbose:
            if not conditional:
                print "\nTASK: %s" % (name)
            else:
                print "\nNOTIFIED: %s" % (name)

        # load up an appropriate ansible runner to
        # run the task in parallel

        runner = ansible.runner.Runner(
            pattern=pattern,
            module_name=module_name,
            module_args=module_args,
            host_list=host_list,
            forks=self.forks,
            remote_pass=self.remote_pass,
            module_path=self.module_path,
            timeout=self.timeout,
            remote_user=remote_user
        )
        results = runner.run()

        # if no hosts are matched, carry on, unlike /bin/ansible
        # which would warn you about this
        if results is None:
            results = {}
 
        # walk through the results and build up
        # summary information about successes and
        # failures.  TODO: split into subfunction

        dark = results.get("dark", [])
        contacted = results.get("contacted", [])
        ok_hosts = contacted.keys()

        for host, msg in dark.items():
            self.processed[host] = 1
            if self.verbose:
                print "unreachable: [%s] => %s" % (host, msg)
            if not self.dark.has_key(host):
                self.dark[host] = 1
            else:
                self.dark[host] = self.dark[host] + 1

        for host, results in contacted.items():
            self.processed[host] = 1
            failed = False
            if module_name == "command":
                if results.get("rc", 0) != 0:
                    failed=True
            elif results.get("failed", 0) == 1:
                    failed=True
   
            if failed:
                if self.verbose:
                    print "failure: [%s] => %s" % (host, results)
                if not self.failures.has_key(host):
                    self.failures[host] = 1
                else:
                    self.failures[host] = self.failures[host] + 1
            else:
                if self.verbose:
                    print "ok: [%s]" % host
                if not self.invocations.has_key(host):
                    self.invocations[host] = 1
                else:
                    self.invocations[host] = self.invocations[host] + 1
                if results.get('changed', False):
                    if not self.changed.has_key(host):
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
            attribs = x["do"]
            name = attribs[0]
            if match_name == name:
                # flag the handler with the list of hosts
                # it needs to be run on, it will be run later
                if not x.has_key("run"):
                    x['run'] = []
                x['run'].append(host)

    def _run_pattern(self, pg):
        '''
        run a list of tasks for a given pattern, in order
        '''

        # get configuration information about the pattern
        pattern  = pg['pattern']
        tasks    = pg['tasks']
        handlers = pg['handlers']
        user     = pg.get('user', C.DEFAULT_REMOTE_USER)

        host_file = pg.get('hosts', '/etc/ansible/hosts')
        self.host_list, groups = ansible.runner.Runner.parse_hosts(host_file)

        if self.verbose:
            print "PLAY: [%s] ********** " % (pattern)

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

 

