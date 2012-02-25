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

        # TODO: return a summary of success & failure counts per node
        # TODO: in bin/ancible, ensure return codes are appropriate

        return "complete"

    def _get_task_runner(self, 
        pattern=None, 
        host_list=None,
        module_name=None, 
        module_args=None):

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

    def _run_task(self, pattern=None, task=None, host_list=None, handlers=None, conditional=False):
        ''' 
        run a single task in the playbook and
        recursively run any subtasks.
        '''

        if host_list is None:
           host_list = self.host_list

        instructions = task['do']
        (comment, module_details) = instructions
        tokens = shlex.split(module_details)
        module_name = tokens[0]
        module_args = tokens[1:]

        namestr = "%s/%s" % (pattern, comment)
        if conditional:
            namestr = "notified/%s" % namestr
        print "TASK [%s]" % namestr

        runner = self._get_task_runner(
            pattern=pattern,
            host_list=host_list, 
            module_name=module_name,
            module_args=module_args
        )
        results = runner.run()
 
        dark = results.get("dark", [])
        contacted = results.get("contacted", [])
        ok_hosts = contacted.keys()

        for host, msg in dark.items():
            print "DARK: [%s] => %s" % (host, msg)

        for host, results in contacted.items():
            if module_name == "command":
               if results.get("rc", 0) != 0:
                  print "FAIL: [%s/%s] => %s" % (host, comment, results)
            elif results.get("failed", 0) == 1:
                  print "FAIL: [%s/%s]" % (host, comment, results)
 

        # flag which notify handlers need to be run
        subtasks = task.get('notify', [])
        if len(subtasks) > 0:
            for host, results in contacted.items():
               if results.get('changed', False):
                  for subtask in subtasks:
                      self._flag_handler(handlers, subtask, host)

        # TODO: if a host fails in any task, remove it from
        # the host list immediately

    def _flag_handler(self, handlers, match_name, host):
        ''' 
        if a task has any notify elements, flag handlers for run
        at end of execution cycle for hosts that have indicated
        changes have been made
        '''
        for x in handlers:
            attribs = x["do"]
            name = attribs[0]
            if match_name == name:
               if not x.has_key("run"):
                  x['run'] = []
               x['run'].append(host)

    def _run_pattern(self, pg):
        '''
        run a list of tasks for a given pattern, in order
        '''

        pattern  = pg['pattern']
        tasks    = pg['tasks']
        handlers = pg['handlers']

        for task in tasks:
            self._run_task(pattern=pattern, task=task, handlers=handlers)
        for task in handlers:
            if type(task.get("run", None)) == list:
                self._run_task(
                   pattern=pattern, 
                   task=task, 
                   handlers=handlers,
                   host_list=task.get('run',[]),
                   conditional=True
                )


 

