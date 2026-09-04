#!/usr/bin/env python
# Copyright (c) 2019 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import base64
import os

import pexpect


input_password = '{{ 1 + 2 }}'

# We use base64 to bypass masking of password. Easier than trying to
# compare in the process and deal with argv and template escaping.
input_password_b64 = base64.b64encode(input_password.encode())

os.environ['ANSIBLE_NOCOLOR'] = '1'
out = pexpect.run(
    'ansible localhost -m debug -a msg="{{ ansible_password | b64encode }}" -k',
    events={
        'SSH password:': f"{input_password}\n"
    }
)

assert input_password_b64 in out
