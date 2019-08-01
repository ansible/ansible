#!/bin/env python

from ansible.module_utils.basic import *

import os, json
import re, sys


def usage_mapping( module ):
    usage = module.params['usage']
    search(module, usage)
    kill(module, usage)
    stop(module, usage)
    resume(module, usage)


def search( module, usage ):
    if usage == "search":
        cpu = module.params['search_method']
        module.exit_json(msg="cpu:  "+usage)


def kill( module, usage ):
    if usage == "kill":
        module.exit_json(msg="TODO: kill method")


def stop( module, usage ):
    if usage == "stop":
        module.exit_json(msg="TODO: stop method")


def resume( module, usage ):
    if usage == "resume":
        module.exit_json(msg="TODO: resume method")


if __name__ == '__main__':
    fields = {
        "usage": {"required": True, "type": "str"},
        "search_method": {"required": False, "type": "str", "default": "general"},
        "user_name": {"required": False, "type": "str", "default": ""},
        "pid": {"required": False, "type": "str", "default": ""},
        "command": {"required": False, "type": "str", "default": ""},
        "start_time": {"required": False, "type": "bool", "default": False},
        "elapsed_time": {"required": False, "type": "bool", "default": False},
        "memory": {"required": False, "type": "bool", "default": False},
        "cpu": {"required": False, "type": "bool", "default": False},
        "ppid": {"required": False, "type": "bool", "default": False},
        "children": {"required": False, "type": "bool", "default": False},
        "threads": {"required": False, "type": "bool", "default": False},
        "elapsed_time_filter": {"required": False, "type": "str", "default": "none"},
        "memory_filter": {"required": False, "type": "str", "default": "none"},
        "cpu_filter": {"required": False, "type": "str", "default": "none"},
    }
    module = AnsibleModule(argument_spec=fields)


    usage_mapping(module)
    module.fail_json(msg=' Usage value can be either "search", "kill", "stop" or "resume" ')

