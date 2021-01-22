# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.common.parameters import (
    get_unsupported_parameters,
    get_type_validator,
)

from ansible.module_utils.common.validation import (
    check_required_arguments
)


class Validator():
    """Argument spec validator class"""

    def __init__(self, arg_spec, module_params):
        self.arg_spec = arg_spec
        self.module_params = module_params
        self.validated_params = {}

    def _check_argument_types(self):
        # FIXME: Need to handle subelements
        for k, v in self.arg_spec.items():
            type = v.get('type', None)
            if k not in self.module_params:
                continue

            value = self.module_params[k]
            if value is None:
                continue

            type_checker, wanted_name = get_type_validator(type)

            self.validated_params[k] = type_checker(value)

    def validate(self):
        """Validate module parameters against argument spec

        arg_spec - dictionary of parameters, type, and valid values
        module_params - dictionary of parameters provided to the module

        Returns validated spec (is there some transformation done? aliases, etc.?)

        Raises TypeError if validation fails.
        """

        # TODO:
        #  - custom exception type for returning _all_ failed validations?

        unsupported_parameters = get_unsupported_parameters(self.arg_spec, self.module_params)
        if unsupported_parameters:
            raise TypeError({'unsupported_params': list(unsupported_parameters)})

        check_required_arguments(self.arg_spec, self.module_params)
        self._check_argument_types()

        return self.validated_params
