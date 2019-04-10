# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


def run_podman_command(module, executable='podman', args=None, expected_rc=0, ignore_errors=False):
    if not isinstance(executable, list):
        command = [executable]
    if args is not None:
        command.extend(args)
    rc, out, err = module.run_command(command)
    if not ignore_errors and rc != expected_rc:
        module.fail_json(
            msg='Failed to run {command} {args}: {err}'.format(
                command=command, args=args, err=err))
    return rc, out, err
