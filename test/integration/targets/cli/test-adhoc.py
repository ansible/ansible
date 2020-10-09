#!/usr/bin/env python
# Copyright (c) 2020 Christoph Schulz <christoph.2.schulz@atos.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

import pexpect

os.environ['ANSIBLE_NOCOLOR'] = '1'
out = pexpect.run(
    'ansible localhost -m debug -a msg="{{ item }}" -L "{{ [1, 2, 3] }}"'
)

for i in [1, 2, 3]:
    assert(('"msg": -%i' % i) in out)
