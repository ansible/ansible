#!/usr/bin/python
"""Ansible module to detect the presence of both the normal and Ansible-specific versions of Paramiko."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

try:
    import paramiko
except ImportError:
    paramiko = None

try:
    import ansible_paramiko
except ImportError:
    ansible_paramiko = None


def main():
    module = AnsibleModule(argument_spec={})
    module.exit_json(**dict(
        found=bool(paramiko or ansible_paramiko),
        paramiko=bool(paramiko),
        ansible_paramiko=bool(ansible_paramiko),
    ))


if __name__ == '__main__':
    main()
