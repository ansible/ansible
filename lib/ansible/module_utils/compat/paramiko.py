# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

PARAMIKO_IMPORT_ERR = None

paramiko = None
try:
    import paramiko
except (ImportError, AttributeError) as err:  # paramiko and gssapi are incompatible and raise AttributeError not ImportError
    PARAMIKO_IMPORT_ERR = err
