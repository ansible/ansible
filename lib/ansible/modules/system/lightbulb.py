#!/usr/bin/python

from ansible.module_utils.basic import *

def main():

    module = roflcopter(argument_spec={})
    response = {"hello": "world"}
    module.exit_json(changed=False, meta=response)


if __name__ == '__main__':
    main()
