# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    strategy: list
    short_description: List tasks
    description:
        - Lists task instead of executing them (mostly), it attempts to run includes and a restricted set of 'non harmful' tasks
          because other tasks can depend on them. For exmple, add_host, include_tasks and include_vars.
    version_added: "2.10"
    author: Ansible Core Team
'''
import sys

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.executor.task_result import TaskResult
from ansible.inventory.host import Host
from ansible.module_utils._text import to_text
from ansible.playbook.included_file import IncludedFile
from ansible.plugins.strategy import StrategyBase
from ansible.plugins.strategy.linear import StrategyModule as LinearStrategy
from ansible.template import Templar
from ansible.utils.display import Display

display = Display()

SAFE_TASKS = ('meta', 'include_tasks', 'include_roles', 'include_vars', 'add_host', 'group_by', 'set_fact')


class StrategyModule(LinearStrategy):

    def __init__(self, tqm):
        super(StrategyModule, self).__init__(tqm)

    def run(self, iterator, play_context):
        '''
        '''

        result = self._tqm.RUN_OK

        # get hosts for play
        self._set_hosts_cache(iterator._play)

        # set forced for listing:
        run_once = True
        any_errors_fatal = False
        ignore_errors = True
        ignore_unreachable = True

        # play tags
        display.display('Play tags: [%s]' % (','.join(iterator._play.tags)))

        # tasks!
        display.display('Tasks:')

        while not self._tqm._terminated:
            try:
                results = []

                # use first host, set for local exec, jic
                # host = Host(iterator._play.hosts.pop())
                host = Host(self._hosts_cache[0])

                # force localhostisms
                host.set_variable('ansible_connection', 'local')
                host.set_variable('ansible_python_interpreter', sys.executable)

                (state, task) = iterator.get_next_task_for_host(host)
                if not task:
                    break
                    continue

                if self._tqm._terminated:
                    break

                if task._role and task._role.has_run(host):
                    # If there is no metadata, the default behavior is to not allow duplicates,
                    # if there is metadata, check to see if the allow_duplicates flag was set to true
                    if task._role._metadata is None or task._role._metadata and not task._role._metadata.allow_duplicates:
                        display.debug("'%s' skipped because role has already run" % task)
                        continue

                if task.action in C._ACTION_META:
                    if task.args.get('_raw_params', None) not in ('reset_connection', 'end_host', 'clear_facts', 'clear_host_errors', 'end_play'):
                        # we skip these for a reason: # end_host to allow listing more tasks,
                        # reset_connection would error out since we are not establishing connections for the hosts, etc
                        results.extend(self._execute_meta(task, play_context, iterator, host))
                    else:
                        results.append(TaskResult(host, task, {'changed': False, 'msg': 'meta action was not really run', 'failed': False}))

                else:
                    task_vars = self._variable_manager.get_vars(play=iterator._play, host=host, task=task, _hosts=self._hosts_cache, _hosts_all=self._hosts_cache_all)
                    self.add_tqm_variables(task_vars, play=iterator._play)
                    templar = Templar(loader=self._loader, variables=task_vars)

                    # template task
                    try:
                        task.name = to_text(templar.template(task.name, fail_on_undefined=False), nonstring='empty')
                    except Exception:
                        # just ignore any errors during task name templating
                        pass

                    # NOTE: don't call 'v2_playbook_on_task_start' or any other events, since we are just listing

                    # queue task if whitelisted
                    if task.action in SAFE_TASKS:
                        self._queue_task(host, task, task_vars, play_context)

                    # TODO: (create list action? push thorugh that?)
                    # print task for list
                    if task.tags:
                        display.display('\t%s\tTAGS: [%s]' % (task.action, ','.join(task.tags)))
                    else:
                        display.display('\t%s' % (task.action))

                    del task_vars

                    results += self._process_pending_results(iterator, max_passes=max(1, int(len(self._tqm._workers) * 0.1)))

                if self._pending_results > 0:
                    results += self._wait_on_pending_results(iterator)

                included_files = IncludedFile.process_include_results(
                    results,
                    iterator=iterator,
                    loader=self._loader,
                    variable_manager=self._variable_manager
                )

                if len(included_files) > 0:

                    all_blocks = dict((host, []) for host in self._hosts_cache)
                    for included_file in included_files:
                        # included hosts get the task list while those excluded get an equal-length
                        # list of noop tasks, to make sure that they continue running in lock-step
                        try:
                            if included_file._is_role:
                                new_ir = self._copy_included_file(included_file)

                                new_blocks, handler_blocks = new_ir.get_block_list(
                                    play=iterator._play,
                                    variable_manager=self._variable_manager,
                                    loader=self._loader,
                                )
                            else:
                                new_blocks = self._load_included_file(included_file, iterator=iterator)

                            for new_block in new_blocks:
                                task_vars = self._variable_manager.get_vars(
                                    play=iterator._play,
                                    task=new_block._parent,
                                    _hosts=self._hosts_cache,
                                    _hosts_all=self._hosts_cache_all,
                                )


                                noop_block = self._prepare_and_create_noop_block_from(new_block, task._parent, iterator)

                                for host in self._hosts_cache:
                                    if host in included_file._hosts:
                                        all_blocks[host].append(new_block)
                                    else:
                                        all_blocks[host].append(noop_block)

                        except AnsibleError as e:
                            display.warning("We were unable to execute the include: %s" % to_text(e))
                            continue

                    for host in self._hosts_cache:
                        iterator.add_tasks(host, all_blocks[host])

                if result != self._tqm.RUN_OK and len(self._tqm._failed_hosts) >= len(self._hosts_cache):
                    display.debug("^ not ok, so returning result now")
                    return result

            except (IOError, EOFError) as e:
                display.debug("got IOError/EOFError in task loop: %s" % e)
                # most likely an abort, return failed
                return self._tqm.RUN_UNKNOWN_ERROR

        # run the base class run() method, which executes the cleanup function
        # and runs any outstanding handlers which have been triggered
        return StrategyBase.run(self, iterator, play_context, result)
