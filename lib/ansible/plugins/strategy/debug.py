
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import cmd
import pprint
import sys

from ansible.plugins.strategy.linear import StrategyModule as LinearStrategyModule
from ansible.compat.six.moves import reduce

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class NextAction(object):
    """ The next action after an interpreter's exit. """
    REDO = 1
    CONTINUE = 2
    EXIT = 3

    def __init__(self, result=EXIT):
        self.result = result


class StrategyModule(LinearStrategyModule):
    def __init__(self, tqm):
        self.curr_tqm = tqm
        super(StrategyModule, self).__init__(tqm)

    def _queue_task(self, host, task, task_vars, play_context):
        self.curr_host = host
        self.curr_task = task
        self.curr_task_vars = task_vars
        self.curr_play_context = play_context

        super(StrategyModule, self)._queue_task(host, task, task_vars, play_context)

    def _process_pending_results(self, iterator, one_pass=False, max_passes=None):
        if not hasattr(self, "curr_host"):
            return super(StrategyModule, self)._process_pending_results(iterator, one_pass, max_passes)

        prev_host_state = iterator.get_host_state(self.curr_host)
        results = super(StrategyModule, self)._process_pending_results(iterator, one_pass)

        while self._need_debug(results):
            next_action = NextAction()
            dbg = Debugger(self, results, next_action)
            dbg.cmdloop()

            if next_action.result == NextAction.REDO:
                # rollback host state
                self.curr_tqm.clear_failed_hosts()
                iterator._host_states[self.curr_host.name] = prev_host_state
                if reduce(lambda total, res : res.is_failed() or total, results, False):
                    self._tqm._stats.failures[self.curr_host.name] -= 1
                elif reduce(lambda total, res : res.is_unreachable() or total, results, False):
                    self._tqm._stats.dark[self.curr_host.name] -= 1

                # redo
                super(StrategyModule, self)._queue_task(self.curr_host, self.curr_task, self.curr_task_vars, self.curr_play_context)
                results = super(StrategyModule, self)._process_pending_results(iterator, one_pass)
            elif next_action.result == NextAction.CONTINUE:
                break
            elif next_action.result == NextAction.EXIT:
                exit(1)

        return results

    def _need_debug(self, results):
        return reduce(lambda total, res : res.is_failed() or res.is_unreachable() or total, results, False)


class Debugger(cmd.Cmd):
    prompt = '(debug) '  # debugger
    prompt_continuous = '> '  # multiple lines

    def __init__(self, strategy_module, results, next_action):
        # cmd.Cmd is old-style class
        cmd.Cmd.__init__(self)

        self.intro = "Debugger invoked"
        self.scope = {}
        self.scope['task'] = strategy_module.curr_task
        self.scope['vars'] = strategy_module.curr_task_vars
        self.scope['host'] = strategy_module.curr_host
        self.scope['result'] = results[0]._result
        self.scope['results'] = results  # for debug of this debugger
        self.next_action = next_action

    def cmdloop(self):
        try:
            cmd.Cmd.cmdloop(self)
        except KeyboardInterrupt:
            pass

    def do_EOF(self, args):
        return self.do_quit(args)

    def do_quit(self, args):
        display.display('aborted')
        self.next_action.result = NextAction.EXIT
        return True

    do_q = do_quit

    def do_continue(self, args):
        self.next_action.result = NextAction.CONTINUE
        return True

    do_c = do_continue

    def do_redo(self, args):
        self.next_action.result = NextAction.REDO
        return True

    do_r = do_redo

    def evaluate(self, args):
        try:
            return eval(args, globals(), self.scope)
        except:
            t, v = sys.exc_info()[:2]
            if isinstance(t, str):
                exc_type_name = t
            else:
                exc_type_name = t.__name__
            display.display('***%s:%s' % (exc_type_name, repr(v)))
            raise

    def do_p(self, args):
        try:
            result = self.evaluate(args)
            display.display(pprint.pformat(result))
        except:
            pass

    def execute(self, args):
        try:
            code = compile(args + '\n', '<stdin>', 'single')
            exec(code, globals(), self.scope)
        except:
            t, v = sys.exc_info()[:2]
            if isinstance(t, str):
                exc_type_name = t
            else:
                exc_type_name = t.__name__
            display.display('***%s:%s' % (exc_type_name, repr(v)))
            raise

    def default(self, line):
        try:
            self.execute(line)
            display.display(pprint.pformat(result))
        except:
            pass
