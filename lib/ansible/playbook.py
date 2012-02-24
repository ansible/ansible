# Copyright (c) 2012 Michael DeHaan <michael.dehaan@gmail.com>
#
# Permission is hereby granted, free of charge, to any person 
# obtaining a copy of this software and associated documentation 
# files (the "Software"), to deal in the Software without restriction, 
# including without limitation the rights to use, copy, modify, merge, 
# publish, distribute, sublicense, and/or sell copies of the Software, 
# and to permit persons to whom the Software is furnished to do so, 
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be 
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR 
# ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import ansible.runner
import ansible.constants as C
import json
import yaml

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

        # runner is reused between calls
 
        self.host_list   = host_list
        self.module_path = module_path
        self.forks       = forks
        self.timeout     = timeout
        self.remote_user = remote_user
        self.remote_pass = remote_pass
        self.verbose     = verbose

        if type(playbook) == str:
            playbook = yaml.load(file(playbook).read())
        self.playbook = playbook
        
    def run(self):
        ''' run against all patterns in the playbook '''

        for pattern in self.playbook:
            self._run_pattern(pattern)
        return "complete"

    def _get_task_runner(self, 
        pattern=None, 
        host_list=None,
        module_name=None, 
        module_args=None):

        print "GET TASK RUNNER FOR HL=%s" % host_list

        ''' 
        return a runner suitable for running this task, using
        preferences from the constructor 
        '''

        if host_list is None:
           host_list = self.host_list

        return ansible.runner.Runner(
            pattern=pattern,
            module_name=module_name,
            module_args=module_args,
            host_list=host_list,
            forks=self.forks,
            remote_user=self.remote_user,
            remote_pass=self.remote_pass,
            module_path=self.module_path,
            timeout=self.timeout
        )

    def _run_task(self, pattern, task, host_list=None):
        ''' 
        run a single task in the playbook and
        recursively run any subtasks.
        '''

        if host_list is None:
           host_list = self.host_list

        print "TASK=%s" % task
        instructions = task['do']
        (comment, module_name, module_args) = instructions
        print "running task: (%s) on hosts matching (%s)" % (comment, pattern)
        runner = self._get_task_runner(
            pattern=pattern,
            host_list=host_list, 
            module_name=module_name,
            module_args=module_args
        )
        results = runner.run()
        print "RESULTS=%s" % results
 
        dark = results.get("dark", [])
        contacted = results.get("contacted", [])

        # TODO: filter based on values that indicate
        # they have changed events to emulate Puppet
        # 'notify' behavior, super easy -- just
        # a list comprehension -- but we need complaint
        # modules first

        ok_hosts = contacted.keys()

        for host, msg in dark.items():
            print "contacting %s failed -- %s" % (host, msg)

        subtasks = task.get('onchange', [])
        if len(subtasks) > 0:
            print "the following hosts have registered change events"
            print ok_hosts
            for subtask in subtasks:
                self._run_task(pattern, subtask, ok_hosts)

        # TODO: if a host fails in task 1, add it to an excludes
        # list such that no other tasks in the list ever execute
        # unlike Puppet, do not allow partial failure of the tree
        # and continuing as far as possible.  Fail fast.


    def _run_pattern(self, pg):
        '''
        run a list of tasks for a given pattern, in order
        '''

        pattern = pg['pattern']
        tasks   = pg['tasks']
        print "PATTERN=%s" % pattern
        print "TASKS=%s" % tasks
        for task in tasks:
            print "*** RUNNING A TASK (%s)***" % task
            self._run_task(pattern, task)



 

