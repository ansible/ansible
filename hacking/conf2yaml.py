#!/usr/bin/env python

import ast
import yaml
import os
import sys
from ansible.parsing.yaml.dumper import AnsibleDumper

things = {}
stuff = {}

op_map = {
    ast.Add: '+',
    ast.Sub: '-',
    ast.Mult: '*',
    ast.Div: '/',
}



def get_values(values):
    if not isinstance(values, list):
        return get_value(values)
    ret = []
    for value in values:
        ret.append(get_value(value))
    return ret


def get_value(value):
    if hasattr(value, 'id'):
        ret = value.id
    elif hasattr(value, 's'):
        ret =  value.s
    elif hasattr(value, 'n'):
        ret = value.n
    elif hasattr(value, 'left'):
        operator = op_map[type(value.op)]
        left = get_values(value.left)
        right = get_values(value.right)
        return '%s %s %s' % (left, operator, right)
    elif hasattr(value, 'value'):
        ret = value.value
    elif hasattr(value, 'elts'):
        ret = get_values(value.elts)
    elif isinstance(value, ast.Call):
        func, args, kwargs = get_call(value)
        args[:] = [repr(arg) for arg in args]
        for k, v in kwargs.items():
            args.append('%s=%s' % (k, repr(v)))
        return '%s(%s)' % (func, ', '.join(args))
    else:
        return value

    return get_value(ret)


def get_call(value):
    args = []
    for arg in value.args:
        v = get_value(arg)
        try:
            v = getattr(C, v, v)
        except:
            pass
        args.append(v)
    kwargs = {}
    for keyword in value.keywords:
        v = get_value(keyword.value)
        try:
            v = getattr(C, v, v)
        except:
            pass
        kwargs[keyword.arg] = v

    func = get_value(value.func)
    try:
        attr = '.%s' % value.func.attr
    except:
        attr = ''
    return '%s%s' % (func, attr), args, kwargs


with open(sys.argv[1]) as f:
    tree = ast.parse(f.read())

for item in tree.body:
    if hasattr(item, 'value') and isinstance(item.value, ast.Call):
        try:
            if item.value.func.id != 'get_config':
                continue
        except AttributeError:
            continue

        _, args, kwargs = get_call(item.value)

        name = get_value(item.targets[0])
        section = args[1].lower()
        config = args[2]

        # new form
        if name not in stuff:
            stuff[name] = {}
        stuff[name] = {
            'desc': 'TODO: write it',
            'ini': [{'section': section, 'key': config}],
            'env': [args[3]],
            'default': args[4] if len(args) == 5 else None,
            'yaml': {'key': '%s.%s' % (section, config)},
            'vars': []
        }
        stuff[name].update(kwargs)

        ## ini like
        #if section not in things:
        #    things[section] = {}

        #things[section][config] = {
        #    'env_var': args[3],
        #    'default': args[4] if len(args) == 5 else 'UNKNOWN'
        #}
        #things[section][config].update(kwargs)
print(yaml.dump(stuff, Dumper=AnsibleDumper, indent=2, width=170))

