# -*- coding: utf-8 -*-
# (c) 2018, Hideki Saito <saito@fgrep.org>
# GNU General Public License v3.0+
#  (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback import CallbackBase

import psutil as ps

DOCUMENTATION = '''
    callback: memory_usage
    callback_type: aggregate
    requirements:
        - whitelist in configuration
        - ps_utils
    short_description: Show memory usage of tasks and handlers
    version_added: "2.6"
    description:
        - This is an ansible callback plugin that profiling memory usage
        - This plugin measures and displays simple memory usage information
        - It is implemented as a decorator in task and handler execution
'''


def _convert_unit(usage):
    """
    Convert memory usage to MiB
    """
    mib = usage / 1024 / 1024
    return mib


def profiling(f=None):
    """
    Decorator that will run the function and print a line-by-line profile
    """
    def wrapper(*args, **kwargs):
        proc = ps.Process()
        val = f(*args, **kwargs)
        results = []
        rss, vms, pfaults, pageins = proc.memory_info()
        print(
            "Memory Usage: rss({rss:.4f})MiB vms({vms:.4f})MiB "
            "pfaults({pfaults:d}) pageins({pageins:d}) @{func}"
            .format(
                rss=_convert_unit(rss),
                vms=_convert_unit(vms),
                pfaults=pfaults,
                pageins=pageins,
                func=f.__name__))
        return val

    return wrapper


class CallbackModule(CallbackBase):
    """
    This callback module tells you how long your plays ran for.
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'memory_usage'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        super(CallbackModule, self).__init__()

    @profiling
    def v2_playbook_on_start(self, playbook):
        pass

    @profiling
    def v2_playbook_on_task_start(self, task, is_conditional):
        pass

    @profiling
    def v2_playbook_on_handler_task_start(self, task):
        pass

#
# [EOF]
#
