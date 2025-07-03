#!/usr/bin/python

from __future__ import annotations


import sys

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(argument_spec={})
    module.exit_json(**dict(found=sys.executable))


if __name__ == '__main__':
    main()
