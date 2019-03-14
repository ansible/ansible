# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class AnsibleModuleError(Exception):
    def __init__(self, results):
        self.results = results

    def __repr__(self):
        return 'AnsibleModuleError(results={0})'.format(self.results)


class AnsibleModuleParameterError(AnsibleModuleError):
    """A module option failed a check"""
    def __init__(self, argument_spec=None, module_parameters=None, requirements=None, results=None):
        self.argument_spec = argument_spec
        self.module_parameters = module_parameters
        self.requirements = requirements

        super(AnsibleModuleParameterError, self).__init__(results=results)
